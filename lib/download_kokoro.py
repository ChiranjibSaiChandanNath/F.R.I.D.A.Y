import os
import sys
import urllib.request

def download_file(url, filepath):
    if os.path.exists(filepath):
        print(f"[INFO] {filepath} already exists. Skipping download.")
        return
    print(f"[INFO] Downloading {url} to {filepath}...")
    try:
        def reporthook(blocknum, blocksize, totalsize):
            readsofar = blocknum * blocksize
            if totalsize > 0:
                percent = readsofar * 1e2 / totalsize
                s = f"\r      {percent:5.1f}% [{readsofar} / {totalsize} bytes]"
                sys.stdout.write(s)
                sys.stdout.flush()
            else:
                sys.stdout.write(f"\r      Read {readsofar} bytes")
                sys.stdout.flush()

        urllib.request.urlretrieve(url, filepath, reporthook)
        print("\n[INFO] Download finished successfully.")
    except Exception as e:
        print(f"\n[ERROR] Failed to download {url}: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        sys.exit(1)

if __name__ == "__main__":
    # URL configurations
    ONNX_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
    BIN_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
    
    # Dest paths
    onnx_dest = "kokoro-v1.0.onnx"
    bin_dest = "voices-v1.0.bin"
    
    download_file(ONNX_URL, onnx_dest)
    download_file(BIN_URL, bin_dest)
