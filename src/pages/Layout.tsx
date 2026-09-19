import { SidebarNav } from "../components/ui/dashboard-sidebar";
import {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  type ReactNode,
} from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  NavLink,
  Outlet,
  useNavigate,
  useParams,
} from "react-router-dom";
import {
  Navigation,
  ArrowUpRight,
  ArrowRight,
  FolderOpen,
  Database,
  Activity,
  FlaskConical,
  Smartphone,
  BookOpen,
  Settings,
  Menu,
  X,
  Plus,
  Upload,
  Play,
  Pause,
  Download,
  ChevronRight,
  Check,
  Radio,
  AlertCircle,
  Search,
  PanelLeftClose,
  RotateCcw,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import {
  api,
  post,
  useResource,
  fmt,
  timeLabel,
  type Project,
  type RecordItem,
  type Job,
} from "../api";
import { ResearchMap, methodColors } from "../components/ResearchMap";



import {Workspace,useWorkspace,useRecords,Notice,Empty,Heading,Status,Field,ProjectRequired,Jobs} from "../ui";
export default function Layout() {
  const projects = useResource<Project[]>("/projects", []);
  const [projectId, setProjectId] = useState(
    localStorage.getItem("waypoint-project") || "",
  );
  const [open, setOpen] = useState(window.innerWidth > 1000);
  const [search, setSearch] = useState("");
  const project =
    projects.data.find((p) => p.id === projectId) || projects.data[0] || null;
  useEffect(() => {
    if (project) localStorage.setItem("waypoint-project", project.id);
  }, [project]);
  return (
    <Workspace.Provider value={{ project, refresh: projects.refresh }}>
      <div className={`app-shell ${open ? "" : "sidebar-collapsed"}`}>
        {open && (
          <>
            <button
              className="sidebar-backdrop"
              aria-label="Close navigation"
              onClick={() => setOpen(false)}
            />
            <SidebarNav projects={projects.data} activeWorkspace={project?.id || ""} onWorkspaceSelect={setProjectId} onClose={() => setOpen(false)} />
          </>
        )}
        <div className="workspace-main">
          <header className="topbar">
            <div>
              <button
                className="icon-button"
                aria-label="Toggle navigation"
                onClick={() => setOpen(!open)}
              >
                <Menu size={19} />
              </button>
              <span className="breadcrumb">
                Workspace <ChevronRight size={13} />
                <strong>{project?.name || "Getting started"}</strong>
              </span>
            </div>
            <div>
              <span className="local-status">
                <i />
                Runs on your computer
              </span>
              <Link to="/app/import" className="button">
                <Plus size={14} />
                Import
              </Link>
            </div>
          </header>
          <main className="main-content">
            {projects.error && (
              <Notice>
                {projects.error}. Start the backend and retry.{" "}
                <button className="text-button" onClick={projects.refresh}>
                  Retry
                </button>
              </Notice>
            )}
            {projects.loading ? (
              <Empty title="Opening your workspace">
                <p>Loading saved projects…</p>
              </Empty>
            ) : (
              <Outlet key={project?.id || "empty"} />
            )}
            <footer className="footer">
              <span>
                <Navigation size={12} />
                Waypoint · Navigation beyond GPS
              </span>
              <span>Local-first research / v1.0</span>
            </footer>
          </main>
        </div>
      </div>
    </Workspace.Provider>
  );
}
