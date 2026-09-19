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
export default function Documentation() {
  return (
    <>
      <Heading
        title="Field notes & documentation"
        description="Understand what the product measures—and what each result means."
      />
      <section className="panel guide">
        <span className="tiny-label">THE WORKING PRINCIPLE</span>
        <h2>A position, built from motion.</h2>
        <p>
          Dead reckoning starts from a known position and uses measured
          acceleration and rotation to estimate movement. Sensor errors
          accumulate. Waypoint compares estimates with recorded GPS while
          keeping that GPS hidden from estimators during selected outages.
        </p>
        <h3>1 / Set up a project</h3>
        <p>
          Create a project, then import a recording. IO-VNBD columns are
          recognized automatically. For your CSV, map timestamps and three
          acceleration/rotation axes. Review units and continuous segments
          before saving.
        </p>
        <h3>2 / Mount and calibrate</h3>
        <p>
          Use a rigid phone mount. The configured phone +Y direction is the
          vehicle forward axis after mounting correction. Begin with a
          stationary period where possible. Save a calibration only from a
          segment with no motion. Initial position, heading and speed must come
          from an available fix or explicit inputs.
        </p>
        <h3>3 / Run an experiment</h3>
        <p>
          Select a recording, outage interval, and optional trained model. The
          worker runs strapdown integration and a 15-state error-state Kalman
          filter. Learned velocity provides an additional filter observation
          when available. A GPS outage removes measurements, not just the status
          badge.
        </p>
        <h3>4 / Train without answer leakage</h3>
        <p>
          Use independent recordings for training, validation and testing.
          Features use only the current and previous five seconds of IMU data.
          GPS speed supplies labels during training, never inference.
          Normalization is learned from training data only. Ridge and CNN–GRU
          models are evaluated on the held-out recording.
        </p>
        <h3>5 / Read the result</h3>
        <p>
          Position RMSE summarizes distance from valid GPS references. Endpoint
          drift reports the last scored sample. With configured outages, metrics
          use outage samples. No valid reference means no accuracy score.
          Normalized drift divides endpoint error by the full reference-route
          distance. Covariance is internal filter uncertainty, not a guaranteed
          confidence interval.
        </p>
        <h3>6 / Record on Android</h3>
        <p>
          Use the APK to collect timestamped IMU/GPS samples. The foreground
          notification keeps recording visible. Local storage comes before
          network transfer; offline sessions can be sent later. Device
          capabilities and timestamps are retained. Live transfer requires the
          computer on the same network.
        </p>
        <h3>Keep results reproducible</h3>
        <p>
          Each result retains its dataset checksum, configuration, model
          reference, and engine version. Export CSV/JSON or a printable report.
          Workspace backup includes recordings and trained artifacts. Restore
          into a new empty directory using scripts/restore.ps1, then start with
          WAYPOINT_DATA set to that path.
        </p>
        <h3>Research boundaries</h3>
        <p>
          This release targets rigidly mounted phones in ground vehicles.
          Smartphone GPS has its own uncertainty. A 10 Hz stream cannot resolve
          vibration above 5 Hz. Long outages and mounting errors can cause
          severe drift; the software reports these results without inventing
          improvements.
        </p>
        <a
          className="button"
          href="https://github.com/onyekpeu/IO-VNBD"
          target="_blank"
          rel="noreferrer"
        >
          Official dataset <ArrowUpRight size={15} />
        </a>
      </section>
    </>
  );
}
