"""
ToDoT CLI - 이미지/동영상을 도트, ASCII, 한글, 유니코드 아트로 변환

사용 예시:
    python src/cli.py input.png -o output.png --mode pixel --pixel-size 8 --colors 16
    python src/cli.py video.mp4 -o result.mp4 --mode ascii --pixel-size 12
    python src/cli.py image.jpg --mode hangul --grid
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
from converter import (
    convert_single_frame, pixelize_image,
    is_image, is_video, MODE_KEYS,
    IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
)


def parse_args():
    parser = argparse.ArgumentParser(
        prog="todot",
        description="ToDoT - 이미지/동영상을 도트, ASCII, 한글, 유니코드 아트로 변환하는 CLI 도구",
    )
    parser.add_argument("input", help="입력 파일 경로 (이미지 또는 동영상)")
    parser.add_argument("-o", "--output", help="출력 파일 경로 (미지정 시 자동 생성)")
    parser.add_argument(
        "-m", "--mode", choices=MODE_KEYS, default="pixel",
        help="변환 모드 (기본값: pixel)"
    )
    parser.add_argument("-p", "--pixel-size", type=int, default=8, help="픽셀 크기 (기본값: 8)")
    parser.add_argument("-c", "--colors", type=int, default=16, help="색상 수 (기본값: 16)")
    parser.add_argument("--grid", action="store_true", help="격자선 표시")
    parser.add_argument("--outline", action="store_true", help="윤곽선 강조")
    parser.add_argument("--output-dir", default=None, help="출력 폴더 (미지정 시 입력 파일 위치)")
    return parser.parse_args()


def generate_output_path(input_path, mode, output_dir=None, ext_override=None):
    base = os.path.splitext(os.path.basename(input_path))[0]
    orig_ext = os.path.splitext(input_path)[1]
    ext = ext_override or orig_ext
    suffix = f"_{mode}" if mode != "pixel" else "_dot"

    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(input_path))

    output_path = os.path.join(output_dir, f"{base}{suffix}{ext}")
    counter = 1
    while os.path.exists(output_path):
        output_path = os.path.join(output_dir, f"{base}{suffix}_{counter}{ext}")
        counter += 1
    return output_path


def convert_image_cli(args):
    print(f"[ToDoT] 이미지 로드: {args.input}")
    img = cv2.imread(args.input, cv2.IMREAD_COLOR)
    if img is None:
        print("[오류] 이미지를 읽을 수 없습니다.", file=sys.stderr)
        return 1

    h, w = img.shape[:2]
    print(f"[ToDoT] 원본 크기: {w}×{h}")
    print(f"[ToDoT] 모드: {args.mode} | 픽셀: {args.pixel_size} | 색상: {args.colors}")

    start = time.time()
    result = convert_single_frame(
        img, args.mode, args.pixel_size, args.colors, args.grid, args.outline
    )
    elapsed = time.time() - start

    if result is None:
        print("[오류] 변환에 실패했습니다.", file=sys.stderr)
        return 1

    output = args.output or generate_output_path(
        args.input, args.mode, args.output_dir, ".png"
    )
    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    cv2.imwrite(output, result)

    rh, rw = result.shape[:2]
    print(f"[ToDoT] 변환 완료 ({elapsed:.2f}초)")
    print(f"[ToDoT] 결과 크기: {rw}×{rh}")
    print(f"[ToDoT] 저장: {output}")
    return 0


def convert_video_cli(args):
    print(f"[ToDoT] 동영상 로드: {args.input}")
    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened():
        print("[오류] 동영상을 열 수 없습니다.", file=sys.stderr)
        return 1

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"[ToDoT] 원본: {w}×{h} | {fps:.1f}FPS | {total}프레임")
    print(f"[ToDoT] 모드: {args.mode} | 픽셀: {args.pixel_size} | 색상: {args.colors}")

    dummy = np.zeros((h, w, 3), dtype=np.uint8)
    test = convert_single_frame(
        dummy, args.mode, args.pixel_size, args.colors, args.grid, args.outline
    )
    out_h, out_w = (test.shape[:2]) if test is not None else (h, w)

    output = args.output or generate_output_path(args.input, args.mode, args.output_dir)
    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)

    ext = os.path.splitext(output)[1].lower()
    fourcc = cv2.VideoWriter_fourcc(*("XVID" if ext == ".avi" else "mp4v"))
    writer = cv2.VideoWriter(output, fourcc, fps, (out_w, out_h))

    start = time.time()
    frame_idx = 0
    last_pct = -1

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        converted = convert_single_frame(
            frame, args.mode, args.pixel_size, args.colors, args.grid, args.outline
        )
        if converted is not None:
            writer.write(converted)

        frame_idx += 1
        if total > 0:
            pct = int(frame_idx / total * 100)
            if pct != last_pct and pct % 5 == 0:
                elapsed = time.time() - start
                remaining = (elapsed / max(frame_idx, 1)) * (total - frame_idx)
                print(f"\r[ToDoT] 진행: {pct}% | 경과: {elapsed:.0f}초 | 남은: ~{remaining:.0f}초", end="", flush=True)
                last_pct = pct

    cap.release()
    writer.release()

    elapsed = time.time() - start
    print(f"\n[ToDoT] 변환 완료 ({elapsed:.1f}초)")
    print(f"[ToDoT] 저장: {output}")
    return 0


def main():
    args = parse_args()

    if not os.path.exists(args.input):
        print(f"[오류] 파일을 찾을 수 없습니다: {args.input}", file=sys.stderr)
        return 1

    if is_image(args.input):
        return convert_image_cli(args)
    elif is_video(args.input):
        return convert_video_cli(args)
    else:
        ext = os.path.splitext(args.input)[1]
        print(f"[오류] 지원하지 않는 파일 형식입니다: {ext}", file=sys.stderr)
        print(f"[지원 이미지] {', '.join(sorted(IMAGE_EXTENSIONS))}")
        print(f"[지원 동영상] {', '.join(sorted(VIDEO_EXTENSIONS))}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
