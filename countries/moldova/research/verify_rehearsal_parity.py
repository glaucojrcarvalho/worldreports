"""Read-only SHA-locked parity audit: research branch vs registered rehearsal."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = "countries/moldova/"
TOPICS = ("economy","fiscal","spending","trade","markets","credit",
          "people","world","demography","security","mortality","migration")
CANDIDATE = ROOT+"research/country_candidate.yaml"
REGISTERED = ROOT+"country.yaml"
PROVENANCE = ROOT+"provenance.json"
CRITICAL = {
 "01-economy": {"macro/economy.csv","macro/national_lfs.csv","world/world.csv"},
 "03-spending": {"fiscal/public_budget.csv","fiscal/nominal_gdp_bns.csv","macro/economy.csv"},
 "06-credit": {"credit/private_credit.csv","credit/prudential_npl.csv"},
 "12-migration": {"demography/demography.csv","migration/migration.csv","migration/foreign_born_census.csv"},
}
DOCS = {"requirements.txt","ADDING_A_COUNTRY.md","SOURCING_A_COUNTRY.md","PLATE_SPINE.md"}

def relevant(path):
    if path.startswith(("core/","site/")) or path in DOCS:
        return True
    return (path.startswith(ROOT) and
            not path.startswith((ROOT+"output/",ROOT+"research/")) and
            path not in (REGISTERED,PROVENANCE))

def expected_graphics():
    return {ROOT+"output/"+("thumbs/" if ext=="thumb" else "")+
            f"{i:02d}-{topic}"+("" if lang=="en" else "."+lang)+
            (".png" if ext=="thumb" else "."+ext)
            for i,topic in enumerate(TOPICS,1)
            for lang in ("ro","en","pt") for ext in ("png","svg","thumb")}

def check(source,rehearsal,provenance):
    shared={p for p in (source.keys() | rehearsal.keys()) if relevant(p)}
    changed=sorted(p for p in shared if source.get(p)!=rehearsal.get(p))
    if changed: raise AssertionError("Rehearsal source drift: "+", ".join(changed[:20]))
    if len(shared)<50 or CANDIDATE not in source:
        raise AssertionError("Insufficient shared source coverage")
    if REGISTERED in source: raise AssertionError("Research unexpectedly registered")
    if rehearsal.get(REGISTERED)!=source[CANDIDATE]:
        raise AssertionError("Rehearsal country.yaml differs from candidate")
    actual={p for p in source if p.startswith(ROOT+"output/")}
    if actual!=expected_graphics():
        raise AssertionError("Missing/extra generated graphics")
    if PROVENANCE not in source: raise AssertionError("Provenance absent")
    keys={f"{i:02d}-{topic}" for i,topic in enumerate(TOPICS,1)}
    if not isinstance(provenance,dict) or set(provenance)!=keys:
        raise AssertionError("Expected 12 plate provenance records")
    refs=set()
    for plate,paths in provenance.items():
        if not isinstance(paths,list) or not paths or len(set(paths))!=len(paths):
            raise AssertionError(f"{plate}: malformed lineage")
        for p in paths:
            if (not isinstance(p,str) or len(Path(p).parts)!=2 or
                ".." in Path(p).parts or "_from_" in p or
                ROOT+"data/"+p not in source):
                raise AssertionError(f"{plate}: unsafe/missing source {p}")
            refs.add(p)
    if len(refs)!=23: raise AssertionError(f"Expected 23 CSVs, got {len(refs)}")
    for plate,paths in CRITICAL.items():
        if set(provenance[plate])!=paths:
            raise AssertionError(f"Source mismatch in {plate}")
    return {"status":"source_rehearsal_parity_pass_not_publication",
            "shared_input_blobs":len(shared),"graphics":len(actual),
            "provenance_plates":len(provenance),"curated_csvs":len(refs),
            "country_config_blob":source[CANDIDATE],
            "critical_sources":{k:sorted(v) for k,v in CRITICAL.items()}}

def git(*args):
    return subprocess.check_output(("git",*args),text=True).strip()

def files(ref):
    entries={}
    for line in git("ls-tree","-r","--full-tree",ref).splitlines():
        header,path=line.split("\t",1)
        mode,kind,sha=header.split()
        if kind=="blob": entries[path]=sha
    return entries

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--source",default="origin/research/moldova-source-audit")
    arg.add_argument("--rehearsal",default="origin/research/moldova-release-rehearsal")
    arg.add_argument("--output",type=Path,default=Path("/tmp/moldova-parity.json"))
    a=arg.parse_args()
    refs=json.loads(git("show",a.source+":"+PROVENANCE))
    result=check(files(a.source),files(a.rehearsal),refs)
    result["source_sha"]=git("rev-parse",a.source)
    result["rehearsal_sha"]=git("rev-parse",a.rehearsal)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("PASS",result)

if __name__=="__main__": main()
