import cv2, glob, numpy as np, os, sys
src, dst = sys.argv[1], sys.argv[2]
fs = sorted(glob.glob(os.path.join(src, "*.png")))
os.makedirs(dst, exist_ok=True)
for k in range(0, len(fs), 4):
    ims = [cv2.resize(cv2.imread(f), (960, 540), interpolation=cv2.INTER_AREA) for f in fs[k:k + 4]]
    while len(ims) < 4:
        ims.append(np.zeros((540, 960, 3), np.uint8))
    sheet = np.vstack([np.hstack(ims[:2]), np.hstack(ims[2:])])
    cv2.line(sheet, (960, 0), (960, 1080), (80, 80, 80), 2); cv2.line(sheet, (0, 540), (1920, 540), (80, 80, 80), 2)
    cv2.imwrite(os.path.join(dst, f"sheet{k // 4}.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
print(len(fs), "stills")
