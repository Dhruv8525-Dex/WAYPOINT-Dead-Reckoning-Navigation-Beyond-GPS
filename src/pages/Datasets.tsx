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
export default function Datasets() {
  const records = useRecords();
  return (
    <>
      <Heading
        title="Recording library"
        description="Measured motion, preserved at the source."
        action={
          <Link to="/app/import" className="button primary">
            <Plus size={15} />
            Import recording
          </Link>
        }
      />
      <ProjectRequired>
        {records.error && <Notice>{records.error}</Notice>}
        <div className="route-grid">
          {records.data
            .filter((r) => r.kind === "dataset")
            .map((r) => (
              <article className="panel route-card" key={r.id}>
                <div className="route-art">
                  <Database size={52} strokeWidth={0.8} />
                  <span>RECORDED SENSOR DATA</span>
                </div>
                <div className="route-content">
                  <span className="tiny-label">
                    {fmt(r.data.sample_rate_hz, 1)} HZ /{" "}
                    {r.data.rows.toLocaleString()} SAMPLES
                  </span>
                  <h2>{r.name}</h2>
                  <p>
                    {r.data.reference_samples.toLocaleString()} GPS reference
                    samples
                  </p>
                  <div className="route-numbers">
                    <span>{timeLabel(r.data.duration_s)}</span>
                    <span>{r.data.warnings.length} quality notes</span>
                  </div>
                  <Link className="button" to={`/app/datasets/${r.id}`}>
                    Inspect recording <ArrowUpRight size={16} />
                  </Link>
                </div>
              </article>
            ))}
        </div>
        {!records.loading &&
          !records.data.some((r) => r.kind === "dataset") && (
            <Empty title="No recordings yet">
              <p>Import a real recording or pair your Android phone.</p>
              <Link to="/app/import" className="button">
                Import your first recording
              </Link>
            </Empty>
          )}
      </ProjectRequired>
    </>
  );
}
