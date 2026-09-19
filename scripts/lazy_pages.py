from pathlib import Path
p=Path('src/App.tsx');s=p.read_text();import re
s='import {lazy,Suspense} from "react";\n'+s
s=re.sub(r'import (\w+) from "(\./pages/[^\"]+)";',r'const \1 = lazy(() => import("\2"));',s)
s=s.replace('<BrowserRouter>','<BrowserRouter><Suspense fallback={<Empty title="Opening page"><p>Loading workspace tools…</p></Empty>}>').replace('</BrowserRouter>','</Suspense></BrowserRouter>');p.write_text(s)
