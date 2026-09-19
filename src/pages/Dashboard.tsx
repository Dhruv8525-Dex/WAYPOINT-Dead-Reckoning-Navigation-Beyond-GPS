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
export default function Dashboard() {
  const { project } = useWorkspace();
  const records = useRecords();
  const jobs = useResource<Job[]>(
    project ? `/jobs?project_id=${project.id}` : null,
    [],
    2000,
  );
  const groups = (kind: string) => records.data.filter((r) => r.kind === kind);
  return (
    <>
      <Heading
        title="Your navigation lab"
        description="Real recordings, working models, and a record of every experiment."
        action={
          <Link className="button primary" to="/app/import">
            <Upload size={15} />
            Import recording
          </Link>
        }
      />
      <ProjectRequired>
        {records.error && <Notice>{records.error}</Notice>}
        <div className="metrics">
          {[
            ["Recordings", groups("dataset").length, "Verified source files"],
            ["Experiments", groups("run").length, "Saved, repeatable results"],
            ["Models", groups("model").length, "Trained on real motion"],
            [
              "Active jobs",
              jobs.data.filter((j) => ["queued", "running"].includes(j.status))
                .length,
              "Local processing queue",
            ],
          ].map(([label, value, note]) => (
            <div className="metric" key={label}>
              <div>
                {label}
                <Activity size={15} />
              </div>
              <strong>{value}</strong>
              <p>{note}</p>
            </div>
          ))}
        </div>
        <div className="dashboard-columns">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>Recent experiments</h2>
                <p>Your latest evidence, ready to explore</p>
              </div>
              <Link to="/app/experiments" className="text-button">
                All experiments <ArrowUpRight size={15} />
              </Link>
            </div>
            {groups("run").length ? (
              groups("run")
                .slice(0, 5)
                .map((r) => (
                  <Link
                    className="list-row"
                    key={r.id}
                    to={`/app/runs/${r.id}`}
                  >
                    <span className="row-icon">
                      <Activity size={19} />
                    </span>
                    <span>
                      <strong>{r.name}</strong>
                      <small>
                        {r.data.dataset_name} ·{" "}
                        {new Date(r.created_at).toLocaleDateString()}
                      </small>
                    </span>
                    <ArrowUpRight size={16} />
                  </Link>
                ))
            ) : (
              <Empty title="Your first experiment starts here">
                <p>
                  Import a recording, then choose an outage to see how
                  positioning behaves.
                </p>
                <Link to="/app/experiments" className="button">
                  Create experiment
                </Link>
              </Empty>
            )}
          </section>
          <section className="insight-panel">
            <span className="tiny-label">A WORKFLOW THAT LEAVES A TRAIL</span>
            <h3>
              Measure it.
              <br />
              Understand it.
              <br />
              Try it again.
            </h3>
            <p>
              Every run keeps its source checksum, settings, and estimator
              version. Your results stay reproducible.
            </p>
            <Link className="button" to="/app/docs">
              Read the research guide <BookOpen size={15} />
            </Link>
          </section>
        </div>
        <Jobs items={jobs.data} refresh={jobs.refresh} />
      </ProjectRequired>
    </>
  );
}
