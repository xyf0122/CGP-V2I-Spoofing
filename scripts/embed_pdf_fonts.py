"""Embed compatible standard-font programs without changing PDF drawing commands."""
from pathlib import Path
from io import BytesIO
import hashlib
import fitz
from pypdf import PdfReader
from fontTools.cffLib import CFFFontSet
from reportlab.pdfbase import _fontdata
mapping={'Helvetica':'helv','Helvetica-Bold':'hebo','Helvetica-Oblique':'heit','Symbol':'symb'}
def embed_pdf(original, path=Path('figure.pdf')):

    d=fitz.open(stream=original,filetype='pdf')
    pending={f[0]: f[3] for p in d for f in p.get_fonts(full=True) if not d.extract_font(f[0])[3]}
    if not pending:
        d.close()
        return original
    reader=PdfReader(BytesIO(original))
    before_text=[p.get_text() for p in d]
    before_pixels=[hashlib.sha256(p.get_pixmap(matrix=fitz.Matrix(3,3)).samples).hexdigest() for p in d]
    before_streams=[p.read_contents() for p in d]
    for xref,base in pending.items():
        assert base in mapping,base
        font=fitz.Font(mapping[base])
        cff=CFFFontSet(); cff.decompile(BytesIO(font.buffer),None)
        name=cff.fontNames[0]
        top=cff[name]
        original_font=reader.get_object(xref)
        encoding=original_font.get('/Encoding')
        if encoding is not None:
            encoding=encoding.get_object()
        if isinstance(encoding,dict):
            enc_name=str(encoding.get('/BaseEncoding','/StandardEncoding')).lstrip('/')
        elif encoding is not None:
            enc_name=str(encoding).lstrip('/')
        else:
            enc_name='SymbolEncoding' if base=='Symbol' else 'StandardEncoding'
        glyphs=list(_fontdata.encodings[enc_name])
        if isinstance(encoding,dict):
            code=0
            for item in encoding.get('/Differences',[]):
                if isinstance(item,int): code=item
                else:
                    glyphs[code]=str(item).lstrip('/')
                    code+=1
        widths=_fontdata.widthsByFontGlyph[base]
        # Explicit widths and glyph names preserve the existing standard-font metrics and encoding.
        width_array='['+' '.join(str(widths.get(g or '.notdef',0)) for g in glyphs)+']'
        differences='[0 '+' '.join('/'+(g or '.notdef') for g in glyphs)+']'
        fontfile=d.get_new_xref()
        d.update_object(fontfile,'<< /Subtype /Type1C >>')
        d.update_stream(fontfile,font.buffer,compress=True)
        descriptor=d.get_new_xref()
        bbox='['+' '.join(str(v) for v in top.FontBBox)+']'
        flags=4 if base=='Symbol' else 32
        if 'Oblique' in base: flags|=64
        d.update_object(descriptor, f'<< /Type /FontDescriptor /FontName /{name} /Flags {flags} /FontBBox {bbox} /ItalicAngle {getattr(top,"ItalicAngle",0)} /Ascent {round(font.ascender*1000)} /Descent {round(font.descender*1000)} /CapHeight 729 /StemV {120 if "Bold" in base else 80} /FontFile3 {fontfile} 0 R >>')
        d.xref_set_key(xref,'BaseFont','/'+name)
        d.xref_set_key(xref,'FontDescriptor',f'{descriptor} 0 R')
        d.xref_set_key(xref,'FirstChar','0')
        d.xref_set_key(xref,'LastChar','255')
        d.xref_set_key(xref,'Widths',width_array)
        d.xref_set_key(xref,'Encoding','<< /Type /Encoding /Differences '+differences+' >>')
    updated=d.tobytes(garbage=4,deflate=True)
    d.close()
    with fitz.open(stream=updated,filetype='pdf') as after:
        assert [p.read_contents() for p in after]==before_streams, (path.name,'drawing commands changed')
        assert [p.get_text() for p in after]==before_text, (path.name,'text changed')
        pixels=[hashlib.sha256(p.get_pixmap(matrix=fitz.Matrix(3,3)).samples).hexdigest() for p in after]
        assert pixels==before_pixels,(path.name,'render differs')
        assert all(after.extract_font(f[0])[3] for p in after for f in p.get_fonts(full=True))
    return updated

if __name__ == '__main__':
    root=Path(__file__).resolve().parents[1]
    for path in (root/'figures').glob('FigR8_downsampling_paired_box_*.pdf'):
        path.write_bytes(embed_pdf(path.read_bytes(),path))
    print('Downsampling figure fonts embedded; appearance verified unchanged.')
