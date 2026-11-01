import os, json, zipfile, hashlib, base64, subprocess
CACHE = os.path.join(os.environ["LOCALAPPDATA"], r"Microsoft.ForzaMotorsport\CmsCache")
ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORACLE = os.path.join(ROOT, r"_tools\cacheoracle\bin\Release\net10.0\cacheoracle.exe")
CMS_ORACLE = os.path.join(ROOT, r"_tools\cmsoracle\bin\Release\net10.0\cmsoracle.exe")
W = os.path.join(ROOT, "_out", "verify"); os.makedirs(W, exist_ok=True)
def b64sha(b): return base64.b64encode(hashlib.sha256(b).digest()).decode()
def run(exe,a):
    r=subprocess.run([exe]+a,capture_output=True,text=True)
    if r.returncode!=0: raise RuntimeError(r.stdout+r.stderr)
cm = os.path.join(CACHE,"cache-manifest.json")
p = os.path.join(W,"cm.json")
run(ORACLE,["dec",cm,p])
man = json.load(open(p,encoding="utf-8"))
print("cache-manifest: OK, entries =", len(man["Files"]))
ok=True
for f in man["Files"]:
    fp = os.path.join(CACHE, f["Path"])
    if not os.path.exists(fp):
        print("  FALTA:", f["Path"]); ok=False; continue
    data=open(fp,"rb").read()
    if len(data)!=f["Size"]: print("  SIZE!=:", f["Path"], len(data), f["Size"]); ok=False
    if b64sha(data)!=f["Checksum"]: print("  CHECKSUM!=:", f["Path"]); ok=False
    bn=os.path.basename(f["Path"])
    if len(bn)==64 and all(c in "0123456789ABCDEF" for c in bn):
        h=hashlib.sha256(data).hexdigest().upper()
        print(("  blob %s  nome==hash? %s" % (bn[:12], "SIM" if h==bn else "NAO (renomeado in-place)")))
for snap in ["20260923t185113xwyk","20251124t234605pkod"]:
    pp=os.path.join(CACHE,"prod",snap)
    prod=json.load(open(pp,encoding="utf-8"))
    pf={x["Path"]:x for x in prod["Files"]}
    bad=0
    for f in prod["Files"]:
        # procura o payload cifrado correspondente em algum blob
        pass
    print(f"prod {snap}: {len(prod['Files'])} arquivos, {len(prod['ContentGroups'])} grupos")
    for n in ("LocStrings_pt-BR.str","BuildersCupScheduleDataV4.json"):
        e=pf[n]; print(f"   {n}: Size={e['Size']} Checksum={e['Checksum'][:20]}...")
print("consistencia do cache-manifest:", "OK" if ok else "FALHOU")
