import re
CHUNK_SIZE = 500; CHUNK_OVERLAP = 80

def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    blocks = re.split(r"\n(?=#{1,4}\s)", text.strip())
    chunks: list[str] = []
    for block in blocks:
        block = block.strip()
        if not block: continue
        if len(block) <= chunk_size:
            chunks.append(block); continue
        start = 0
        while start < len(block):
            piece = block[start : start + chunk_size]
            if piece.strip(): chunks.append(piece.strip())
            start += chunk_size - overlap
    return chunks
