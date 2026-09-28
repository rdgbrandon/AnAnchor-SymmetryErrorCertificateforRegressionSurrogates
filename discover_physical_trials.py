"""Inspect public archive metadata only; never download a 190-GB archive.

Reads ZIP local headers until the first data payload. Does not open trial
measurements. Saves reproducible provenance and byte-range availability.
"""
import hashlib
import json
import struct
import urllib.request
import zlib
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUT=HERE/'external_trials'
BASE='https://library.ucsd.edu/dc/object/bb9811148n'
LEVELS=[0.,.00025,.00066,.00067,.00083,.00115,.00156,.00176,.00199,.00284,.00332]


def inspect(index, ca):
    url=BASE+'/_%d_1.zip/download'%index
    # A suffix range would expose the directory, if the server supports ranges.
    req=urllib.request.Request(url,headers={'Range':'bytes=-65558'})
    with urllib.request.urlopen(req,timeout=30) as r:
        status=r.status
        headers={k:r.headers.get(k) for k in ['Content-Length','Content-Range','Content-Type']}
        if status==206:
            return dict(url=url,ca=ca,http_status=status,headers=headers,
                        action='Range access available; implement selective ZIP retrieval before loading targets.')
        if status!=200 or r.headers.get('Content-Type')!='application/zip':
            raise ValueError('Unexpected archive response')
        names=[];metadata={};consumed=0
        for _ in range(256):
            header=r.read(30);consumed+=len(header)
            if len(header)!=30 or header[:4]!=b'PK\x03\x04': break
            a=struct.unpack('<4s5H3I2H',header)
            flags,method,crc,compressed,nlen,elen=a[2],a[3],a[6],a[7],a[9],a[10]
            name=r.read(nlen).decode('utf-8');r.read(elen);consumed+=nlen+elen
            names.append(name)
            if name.endswith('/') and compressed==0: continue
            if not name.endswith('.md') or compressed>65536 or flags&8: break
            raw=r.read(compressed);consumed+=len(raw)
            content=zlib.decompress(raw,-15) if method==8 else raw
            if zlib.crc32(content)&0xffffffff != crc: raise ValueError('Metadata CRC mismatch')
            metadata[name]=content.decode('utf-8')
        return dict(url=url,ca=ca,http_status=status,headers=headers,bytes_read=consumed,
                    prefix_members=names,metadata=metadata,
                    repeat_directories=[n for n in names if '/rep' in n and n.endswith('/')],
                    status='Metadata only. Range ignored; large HDF5 payload precedes accessible CSV files.')


def run():
    OUT.mkdir(exist_ok=True)
    with urllib.request.urlopen(BASE,timeout=30) as r: page=r.read()
    (OUT/'source_metadata.html').write_bytes(page)
    archives=[]
    for i,ca in enumerate(LEVELS,1):
        try: entry=inspect(i,ca)
        except Exception as e: entry=dict(ca=ca,error=str(e))
        archives.append(entry);print(ca,len(entry.get('repeat_directories',[])),entry.get('status',entry.get('error')),flush=True)
    manifest=dict(doi='10.6075/J0K07581',source=BASE,
        attribution='Zhang, Lei; Kim, Hyeonghun; Kramer, Boris; Friend, James (2026). Water Surface Data. UC San Diego Library Digital Collections.',
        license='CC BY 4.0',date_collected='2025-08 to 2025-12',
        checked_utc=datetime.now(timezone.utc).isoformat(),
        metadata_sha256=hashlib.sha256(page).hexdigest(),archives=archives,
        new_trials_scored=0,
        caveat='Distinct collection dates establish new recordings, not independent apparatus or IID experimental conditions.')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')


if __name__=='__main__':run()
