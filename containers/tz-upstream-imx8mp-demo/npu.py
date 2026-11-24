#!/usr/bin/env python3
"""NPU demo: run TensorFlow Lite models on the NPU through Mesa's Teflon delegate.

  npu.py classify [IMAGE]   MobileNet V1 on the CPU and on the NPU: top 3 classes, time, speed-up
  npu.py detect [IMAGE]     SSD MobileNet V2 (COCO) on the NPU: objects found, compared with the CPU
  npu.py loop SECONDS       classify without pause on the NPU, check every result against the CPU

Prints one "RESULT npu-<test> PASS|FAIL ..." line per test for tz-demo.
"""
import os
import sys
import time

import numpy as np
from PIL import Image
from ai_edge_litert.interpreter import Interpreter, load_delegate

DATA = "/opt/demo"
DELEGATE = os.environ.get("TEFLON_DELEGATE", "/opt/mesa/lib/libteflon.so")
IMAGE = os.path.join(DATA, "grace_hopper.bmp")
CLASSIFIER = "mobilenet_v1_1.0_224_quant.tflite"
DETECTOR = "ssd_mobilenet_v2_coco_quant_postprocess.tflite"


def labels(name):
    with open(os.path.join(DATA, "models", name)) as f:
        return [line.strip() for line in f]


def interpreter(model, npu):
    delegates = [load_delegate(DELEGATE)] if npu else []
    it = Interpreter(os.path.join(DATA, "models", model), experimental_delegates=delegates, num_threads=4)
    it.allocate_tensors()
    return it


def set_input(it, image):
    d = it.get_input_details()[0]
    _, h, w, _ = d["shape"]
    a = np.asarray(image.convert("RGB").resize((w, h)), dtype=np.uint8)
    if d["dtype"] == np.int8:
        a = (a.astype(np.int16) - 128).astype(np.int8)
    it.set_tensor(d["index"], a[None])


def timed(it, runs):
    it.invoke()  # the first run on the NPU compiles the graph
    t = []
    for _ in range(runs):
        s = time.perf_counter()
        it.invoke()
        t.append((time.perf_counter() - s) * 1000)
    return float(np.median(t))


def scores(it):
    o = it.get_output_details()[0]
    s = it.get_tensor(o["index"])[0].astype(np.float32)
    scale, zero = o["quantization"]
    return (s - zero) * scale if scale else s


def detections(it, thresh=0.5):
    out = sorted(it.get_output_details(), key=lambda o: o["index"])
    boxes, classes, sc = (it.get_tensor(out[i]["index"])[0] for i in range(3))
    return [(int(c) if np.isfinite(c) else -1, float(s), b) for b, c, s in zip(boxes, classes, sc) if s >= thresh]


def classify(path):
    img, names = Image.open(path), labels("imagenet_labels.txt")
    res = {}
    for npu in (False, True):
        it = interpreter(CLASSIFIER, npu)
        set_input(it, img)
        ms = timed(it, 20 if npu else 5)
        res[npu] = (ms, scores(it))
    print(f"MobileNet V1 on {os.path.basename(path)}")
    for npu, (ms, s) in res.items():
        top = np.argsort(s)[::-1][:3]
        print(f"  {'NPU' if npu else 'CPU'}: {ms:6.2f} ms   " + ", ".join(f"{names[i].split(',')[0]} {s[i]:.2f}" for i in top))
    same = res[False][1].argmax() == res[True][1].argmax()
    print(f"RESULT npu-classify {'PASS' if same else 'FAIL'} {res[True][0]:.2f} ms on the NPU, "
          f"x{res[False][0] / res[True][0]:.1f} faster than the CPU, top-1 {'same as' if same else 'DIFFERS from'} the CPU")
    return same


def iou(a, b):
    h = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    w = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - h * w
    return h * w / u if u > 0 else 0.0


def detect(path):
    img, coco = Image.open(path), labels("coco_labels.txt")

    def name(c):
        return coco[c] if 0 <= c < len(coco) else f"class {c}"

    res = {}
    for npu in (False, True):
        it = interpreter(DETECTOR, npu)
        set_input(it, img)
        ms = timed(it, 10 if npu else 3)
        res[npu] = (ms, detections(it))
    print(f"SSD MobileNet V2 on {os.path.basename(path)}, score >= 0.5")
    for npu, (ms, dets) in res.items():
        print(f"  {'NPU' if npu else 'CPU'}: {ms:6.2f} ms   " +
              (", ".join(f"{name(c)} {s:.2f}" for c, s, _ in dets) or "nothing"))
    cpu, npu = res[False][1], res[True][1]
    found = sum(any(c == c2 and iou(b, b2) >= 0.5 for c2, _, b2 in npu) for c, _, b in cpu)
    ok = len(cpu) > 0 and found == len(cpu)
    print(f"RESULT npu-detect {'PASS' if ok else 'FAIL'} {res[True][0]:.2f} ms on the NPU, "
          f"{found}/{len(cpu)} CPU objects found by the NPU")
    return ok


def loop(seconds):
    img = Image.open(IMAGE)
    ref = interpreter(CLASSIFIER, False)
    set_input(ref, img)
    ref.invoke()
    want = scores(ref).argmax()
    it = interpreter(CLASSIFIER, True)
    set_input(it, img)
    n = good = 0
    end = time.monotonic() + seconds
    start = time.monotonic()
    while time.monotonic() < end:
        it.invoke()
        n += 1
        good += scores(it).argmax() == want
    rate = n / (time.monotonic() - start)
    ok = n > 0 and good == n
    print(f"RESULT npu-loop {'PASS' if ok else 'FAIL'} {n} inferences, {rate:.0f} per second, "
          f"{good}/{n} same top-1 as the CPU")
    return ok


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "classify"
    if cmd == "classify":
        ok = classify(sys.argv[2] if len(sys.argv) > 2 else IMAGE)
    elif cmd == "detect":
        ok = detect(sys.argv[2] if len(sys.argv) > 2 else IMAGE)
    elif cmd == "loop":
        ok = loop(float(sys.argv[2]) if len(sys.argv) > 2 else 30)
    else:
        print(__doc__)
        return 2
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
