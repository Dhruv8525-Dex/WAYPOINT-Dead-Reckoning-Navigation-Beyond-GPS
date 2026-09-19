from pathlib import Path
p=Path('src/App.tsx');s=p.read_text()
page_names=['Layout','Landing','Dashboard','Projects','Datasets','ImportPage','DatasetDetail','Experiments','RunDetail','Models','Devices','Documentation','SettingsPage']
common_names=['Notice','Empty','Heading','Status','Field','ProjectRequired','Jobs']
import re
matches=list(re.finditer(r'^function (\w+)\(',s,re.M));blocks={}
for i,m in enumerate(matches):
    end=matches[i+1].start() if i+1<len(matches) else s.index('export default function App')
    blocks[m.group(1)]=s[m.start():end]
# The only inter-function helper is useRecords; export it through the shared UI module.
imports=s[:s.index('const Workspace')]
context=s[s.index('const Workspace'):s.index('function Notice')]
context=context.replace('const Workspace','export const Workspace').replace('const useWorkspace','export const useWorkspace')
common_imports=imports.replace('"./api"','"./api"').replace('import { SidebarNav } from "./components/ui/dashboard-sidebar";','')
common=context
for name in common_names:
    block=blocks[name]
    if name=='ProjectRequired':
        block=block[:block.find('const navigation')] if 'const navigation' in block else block
    common+=block.replace('function '+name,'export function '+name,1)
# useRecords is a function block itself after ProjectRequired in the formatted source.
if 'useRecords' in blocks: common+=blocks['useRecords'].split('const navigation')[0].replace('function useRecords','export function useRecords',1)
Path('src/ui.tsx').write_text(common_imports+common)
Path('src/pages').mkdir(exist_ok=True)
universal=imports.replace('"./api"','"../api"').replace('"./components/ResearchMap"','"../components/ResearchMap"').replace('"./components/ui/dashboard-sidebar"','"../components/ui/dashboard-sidebar"').replace('import "./product.css";','')
universal+='\nimport {Workspace,useWorkspace,useRecords,Notice,Empty,Heading,Status,Field,ProjectRequired,Jobs} from "../ui";\n'
for name in page_names:
    block=blocks[name]
    Path(f'src/pages/{name}.tsx').write_text(universal+block.replace('function '+name,'export default function '+name,1))
router=s[s.index('export default function App'):]
p.write_text('import {BrowserRouter,Routes,Route,Link} from "react-router-dom";\nimport {Empty} from "./ui";\nimport "./product.css";\n'+''.join(f'import {name} from "./pages/{name}";\n' for name in page_names)+router)
