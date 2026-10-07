"""Build small synthetic PDFs in memory, with no third-party dependency.

Used by tests and by ``scripts/make_synthetic_bundle.py``. All content is
invented. Text pages use the standard Helvetica font, so pypdf extracts the
lines back in order. ``IMAGE`` pages contain only a tiny grey image (no text
layer), like a photographed document; ``BLANK`` pages contain nothing.
"""

from dataclasses import dataclass
from typing import Literal

PageSpec = list[str] | Literal["IMAGE", "BLANK"]

_PAGE_WIDTH, _PAGE_HEIGHT = 595, 842


def _escape(line: str) -> str:
    return line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _text_stream(lines: list[str]) -> bytes:
    parts = ["BT", "/F1 10 Tf", "14 TL", f"50 {_PAGE_HEIGHT - 60} Td"]
    for line in lines:
        parts.append(f"({_escape(line)}) Tj T*")
    parts.append("ET")
    return "\n".join(parts).encode("latin-1")


@dataclass
class _Writer:
    objects: list[bytes]

    def add(self, body: bytes) -> int:
        self.objects.append(body)
        return len(self.objects)

    def stream(self, data: bytes, extra: str = "") -> int:
        head = f"<< /Length {len(data)} {extra}>>\nstream\n".encode()
        return self.add(head + data + b"\nendstream")

    def render(self, root: int) -> bytes:
        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for number, body in enumerate(self.objects, start=1):
            offsets.append(len(out))
            out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
        xref = len(out)
        out += f"xref\n0 {len(self.objects) + 1}\n0000000000 65535 f \n".encode()
        for offset in offsets:
            out += f"{offset:010d} 00000 n \n".encode()
        out += f"trailer\n<< /Size {len(self.objects) + 1} /Root {root} 0 R >>\n".encode()
        out += f"startxref\n{xref}\n%%EOF\n".encode()
        return bytes(out)


def build_pdf(pages: list[PageSpec]) -> bytes:
    writer = _Writer([])
    font = writer.add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    image = writer.stream(
        bytes([90, 160, 160, 90]),
        "/Type /XObject /Subtype /Image /Width 2 /Height 2 /ColorSpace /DeviceGray /BitsPerComponent 8 ",
    )
    pages_id = len(writer.objects) + 1 + 2 * len(pages)  # reserved after page objects
    page_ids = []
    for spec in pages:
        if spec == "BLANK":
            content = writer.stream(b"")
            resources = "<< >>"
        elif spec == "IMAGE":
            content = writer.stream(b"q 400 0 0 500 90 170 cm /Im1 Do Q")
            resources = f"<< /XObject << /Im1 {image} 0 R >> >>"
        else:
            content = writer.stream(_text_stream(list(spec)))
            resources = f"<< /Font << /F1 {font} 0 R >> >>"
        page_ids.append(
            writer.add(
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {_PAGE_WIDTH} "
                f"{_PAGE_HEIGHT}] /Resources {resources} /Contents {content} 0 R >>".encode()
            )
        )
    kids = " ".join(f"{p} 0 R" for p in page_ids)
    assert writer.add(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode()) == pages_id
    root = writer.add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode())
    return writer.render(root)
