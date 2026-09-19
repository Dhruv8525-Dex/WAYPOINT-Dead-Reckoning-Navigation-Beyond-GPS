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
export default function Projects() {
  const { refresh } = useWorkspace();
  const list = useResource<Project[]>("/projects", []);
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const create = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const values = new FormData(form);
    setBusy(true);
    try {
      await post("/projects", {
        name: values.get("name"),
        description: values.get("description"),
      });
      form.reset();
      refresh();
      list.refresh();
      setError("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <Heading
        title="Projects"
        description="Keep each research question in its own workspace."
      />
      <div className="dashboard-columns">
        <section className="panel form-panel">
          <h2>Create a project</h2>
          <form onSubmit={create}>
            <Field label="Project name">
              <input
                name="name"
                required
                maxLength={120}
                placeholder="Urban navigation study"
              />
            </Field>
            <Field label="Research question">
              <textarea
                name="description"
                maxLength={2000}
                placeholder="What do you want to investigate?"
              />
            </Field>
            {error && <Notice>{error}</Notice>}
            <button disabled={busy} className="button primary">
              {busy ? "Creating…" : "Create project"}
              <Plus size={15} />
            </button>
          </form>
        </section>
        <section className="panel">
          <div className="panel-heading">
            <h2>Saved projects</h2>
          </div>
          {list.data.map((p) => (
            <div className="list-row" key={p.id}>
              <FolderOpen size={20} />
              <span>
                <strong>{p.name}</strong>
                <small>{p.description || "No description"}</small>
              </span>
            </div>
          ))}
          {!list.data.length && (
            <Empty title="Make room for your research">
              <p>
                Create a project to organize datasets, models, and experiments.
              </p>
            </Empty>
          )}
        </section>
      </div>
    </>
  );
}
