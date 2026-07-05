import os
from functools import lru_cache

from app.config import get_settings


CHUNK_SIZE = 1200
CHUNK_OVERLAP = 180


def _chunk_text(content):
    if len(content) <= CHUNK_SIZE:
        return [content]

    chunks = []
    start = 0
    while start < len(content):
        end = min(start + CHUNK_SIZE, len(content))
        if end < len(content):
            boundary = max(content.rfind("\n", start, end), content.rfind(". ", start, end))
            if boundary > start + CHUNK_SIZE // 2:
                end = boundary + 1
        chunk = content[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(content):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


@lru_cache(maxsize=1)
def load_documents(data_path=None):
    settings = get_settings()
    base_path = data_path or str(settings["data_dir"])
    documents = []
    allowed_extensions = {
        ".txt", ".md", ".json", ".yaml", ".yml", ".log", ".cfg", ".conf",
        ".ini", ".tf", ".hcl", ".py", ".js", ".ts", ".sql", ".xml", ".csv",
        ".pdf",
    }

    for root, _, files in os.walk(base_path):
        for file in files:
            file_path = os.path.join(root, file)
            extension = os.path.splitext(file)[1].lower()
            if extension and extension not in allowed_extensions:
                continue

            try:
                filename = os.path.basename(file_path)
                if extension == ".pdf":
                    try:
                        import pypdf
                        reader = pypdf.PdfReader(file_path)
                        content = ""
                        for page in reader.pages:
                            text = page.extract_text()
                            if text:
                                content += text + "\n"
                    except ImportError:
                        print(f"pypdf is not installed; skipping PDF file: {file_path}")
                        continue
                else:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                for index, chunk in enumerate(_chunk_text(content), start=1):
                    documents.append({
                        "content": chunk,
                        "source": f"{file_path}#chunk-{index}",
                        "source_path": file_path,
                        "filename": filename,
                        "chunk_id": index,
                    })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    return documents
