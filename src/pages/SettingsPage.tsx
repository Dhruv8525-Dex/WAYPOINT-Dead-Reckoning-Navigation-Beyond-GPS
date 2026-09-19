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
  downloadResource,
  type Project,
  type RecordItem,
  type Job,
} from "../api";
import { ResearchMap, methodColors } from "../components/ResearchMap";



import {Workspace,useWorkspace,useRecords,Notice,Empty,Heading,Status,Field,ProjectRequired,Jobs} from "../ui";
export default function SettingsPage() {
  const health = useResource<any>("/health", null);
  const [error, setError] = useState("");
  const backup = async () => {
    try {
      await downloadResource("/backup", "waypoint-backup.zip");
    } catch (e) {
      setError((e as Error).message);
    }
  };
  return (
    <>
      <Heading
        title="Workspace settings"
        description="A local workspace you can inspect, preserve, and restore."
      />
      <div className="dashboard-columns">
        <section className="panel form-panel">
          <h2>Storage & backup</h2>
          <p className="helper-text">
            Create a consistent archive after all jobs finish. It includes
            source recordings, processed data, models, and results.
          </p>
          {error && <Notice>{error}</Notice>}
          <button className="button primary" onClick={backup}>
            <Download size={15} />
            Download workspace backup
          </button>
          <h3 className="section-title">Restore without overwriting</h3>
          <p className="helper-text">
            Run scripts/restore.ps1 with your backup and a new empty
            destination. Start the app with WAYPOINT_DATA set to that folder.
            Re-pair devices after restoration.
          </p>
        </section>
        <section className="panel form-panel">
          <h2>System status</h2>
          {health.error ? (
            <Notice>{health.error}</Notice>
          ) : (
            <dl className="metadata">
              <dt>Backend</dt>
              <dd>{health.data?.status || "Checking…"}</dd>
              <dt>Version</dt>
              <dd>{health.data?.version}</dd>
              <dt>Mode</dt>
              <dd>Single-user / local only</dd>
              <dt>Data location</dt>
              <dd className="checksum">{health.data?.data_dir}</dd>
            </dl>
          )}
        </section>
      </div>
    </>
  );
}
