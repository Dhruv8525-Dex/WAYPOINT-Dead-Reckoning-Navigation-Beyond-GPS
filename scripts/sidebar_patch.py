from pathlib import Path
p=Path('src/App.tsx');s=p.read_text();s='import { SidebarNav } from "./components/ui/dashboard-sidebar";\n'+s
start=s.index('            <aside className="sidebar">');end=s.index('            </aside>',start)+len('            </aside>')
s=s[:start]+'            <SidebarNav projects={projects.data} activeWorkspace={project?.id || ""} onWorkspaceSelect={setProjectId} onClose={() => setOpen(false)} />'+s[end:];p.write_text(s)
p=Path('src/api.ts');s=p.read_text();s='import type { components } from "./api-schema";\n'+s
start=s.index('export type Project =');end=s.index('export type RecordItem',start)
s=s[:start]+'export type Project = components["schemas"]["ProjectOut"];\n'+s[end:];p.write_text(s)
