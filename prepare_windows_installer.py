"""Build an unsigned preview EXE from explicitly checked public sources."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import prepare_release as release
import verifier_avant_github as guard

ROOT=Path(__file__).resolve().parent

def checked_files(additional=()):
    files=set(release.lister_fichiers_suivis())
    files.update(Path(name) for name in additional)
    files=sorted(files,key=lambda p:p.as_posix())
    release.verifier_liste_archive(files)
    names=[p.as_posix() for p in files]
    if guard.verifier_fichiers_hors_perimetre_suivis(names) or guard.verifier_fichiers_sensibles_suivis(names) or guard.verifier_contenu_secret(names):
        raise RuntimeError('Public-source validation failed; installer not built')
    return files

def build(compiler,output,additional=(),smoke=False):
    compiler=Path(compiler).resolve();output=Path(output).resolve()
    if not compiler.is_file():raise ValueError('Inno Setup compiler not found')
    files=checked_files(additional)
    script=ROOT/'installer/windows/gruterra_preview.iss'
    if guard.problemes_valeurs('installer/windows/gruterra_preview.iss',script.read_text(encoding='utf-8-sig')):
        raise RuntimeError('Installer script contains a sensitive value')
    version=(ROOT/'VERSION').read_text(encoding='utf-8-sig').strip()
    output.mkdir(parents=True,exist_ok=True)
    name='Gruterra-Setup-'+version+'-candidate'+('-smoke' if smoke else '')
    with tempfile.TemporaryDirectory(prefix='gruterra installer build ') as directory:
        temp=Path(directory);payload=temp/'payload';payload.mkdir()
        entries=[]
        for relative in files:
            dest=payload/relative;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/relative,dest)
            parent=str(relative.parent).replace('/','\\')
            app='{app}' if parent=='.' else '{app}\\'+parent
            entries.append('Source: "'+str(dest)+'"; DestDir: "'+app+'"; Flags: ignoreversion')
        listing=temp/'payload_files.iss';listing.write_text('\n'.join(entries)+'\n',encoding='utf-8-sig')
        command=[str(compiler),'/Qp','/DBuildVersion='+version,'/DOutputDirectory='+str(output),
                 '/DOutputName='+name,'/DFileList='+str(listing)]
        if smoke:command.append('/DSmokeTest=1')
        command.append(str(ROOT/'installer/windows/gruterra_preview.iss'))
        result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
        if result.returncode:
            print(result.stdout[-6000:]);print(result.stderr[-3000:])
            raise RuntimeError('Preview compilation failed')
    exe=output/(name+'.exe')
    if not exe.is_file():raise RuntimeError('Compiler did not produce expected EXE')
    report={'preview':True,'signed':False,'published':False,'source_version':version,
            'payload_files':len(files),'smoke_layout':smoke,'sha256':release.calculer_sha256(exe)}
    exe.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return exe,report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',required=True)
    parser.add_argument('--output',default=str(ROOT/'_dist'))
    parser.add_argument('--additional-file',action='append',default=[])
    parser.add_argument('--smoke',action='store_true',help='Shortcuts stay in test folder, no uninstall registry entry')
    args=parser.parse_args()
    exe,report=build(args.compiler,args.output,args.additional_file,args.smoke)
    print('Unsigned local preview:',exe)
    print(json.dumps(report))
if __name__=='__main__':main()
