
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
} from "./api";
import { ResearchMap, methodColors } from "./components/ResearchMap";
import "./product.css";

export const Workspace = createContext<{
  project: Project | null;
  refresh: () => void;
}>({ project: null, refresh: () => {} });
export const useWorkspace = () => useContext(Workspace);
export function Notice({ children }: { children: ReactNode }) {
  return (
    <div className="notice" role="alert">
      <AlertCircle size={16} />
      <span>{children}</span>
    </div>
  );
}
export function Empty({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="empty">
      <Navigation size={30} />
      <h2>{title}</h2>
      <div>{children}</div>
    </div>
  );
}
export function Heading({
  eyebrow = "WAYPOINT / RESEARCH WORKSPACE",
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  );
}
export function Status({ value }: { value: string }) {
  return (
    <span className={`status status-${value}`}>
      {value.replaceAll("_", " ")}
    </span>
  );
}
export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: ReactNode;
  hint?: string;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint && <small>{hint}</small>}
    </label>
  );
}
export function ProjectRequired({ children }: { children: ReactNode }) {
  const { project } = useWorkspace();
  return project ? (
    <>{children}</>
  ) : (
    <Empty title="Start with a project">
      <p>A project keeps your recordings, models, and experiments together.</p>
      <Link className="button primary" to="/app/projects">
        Create a project <ArrowRight size={15} />
      </Link>
    </Empty>
  );
}
export function Jobs({ items, refresh }: { items: Job[]; refresh: () => void }) {
  const [error, setError] = useState("");
  return (
    <section className="panel jobs-panel">
      <div className="panel-heading">
        <h2>Processing queue</h2>
        <span className="soft-tag">Local worker</span>
      </div>
      {error && <Notice>{error}</Notice>}
      {items.slice(0, 12).map((j) => (
        <div className="job-row" key={j.id}>
          <div>
            <strong>{j.config.name}</strong>
            <small>{j.message}</small>
            {["running", "queued", "cancel_requested"].includes(j.status) && (
              <progress
                max="100"
                value={j.progress}
                aria-label={`${j.config.name} progress`}
              />
            )}
          </div>
          <Status value={j.status} />
          {["queued", "running"].includes(j.status) && (
            <button
              className="button"
              onClick={async () => {
                try {
                  await post(`/jobs/${j.id}/cancel`, {});
                  refresh();
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            >
              Cancel
            </button>
          )}
          {j.result_id && (
            <Link
              className="text-button"
              to={j.kind === "run" ? `/app/runs/${j.result_id}` : "/app/models"}
            >
              View result <ArrowUpRight size={15} />
            </Link>
          )}
        </div>
      ))}
      {!items.length && (
        <p className="helper-text padded">
          No queued jobs. Create an experiment or train a model to begin.
        </p>
      )}
    </section>
  );
}
export function useRecords() {
  const { project } = useWorkspace();
  return useResource<RecordItem[]>(
    project ? `/records?project_id=${project.id}` : null,
    [],
    4000,
  );
}
