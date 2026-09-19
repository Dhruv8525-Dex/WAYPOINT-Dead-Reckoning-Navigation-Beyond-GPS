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
export default function DatasetDetail() {
  const { id } = useParams();
  const detail = useResource<RecordItem | null>(`/records/${id}`, null);
  const samples = useResource<any[]>(`/datasets/${id}/samples`, []);
  const { project } = useWorkspace();
  const [error, setError] = useState(""),
    [saved, setSaved] = useState(""),
    [busy, setBusy] = useState(false);
  const row = detail.data;
  const paths = useMemo(
    () => ({
      reference: {
        lat: samples.data.map((s) => s.lat),
        lng: samples.data.map((s) => s.lng),
      },
    }),
    [samples.data],
  );
  const calibrate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    setBusy(true);
    try {
      const r = await post("/calibrations", {
        project_id: project!.id,
        dataset_id: id,
        name: data.get("name"),
        start: Number(data.get("start")),
        end: Number(data.get("end")),
      });
      setSaved(r.name);
      setError("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  if (detail.error) return <Notice>{detail.error}</Notice>;
  if (!row)
    return (
      <Empty title="Loading recording">
        <p>Reading the source profile…</p>
      </Empty>
    );
  return (
    <>
      <Heading
        title={row.name}
        description="Inspect signal quality before using this recording in an experiment."
        action={
          <Link
            to={`/app/experiments?dataset=${id}`}
            className="button primary"
          >
            Create experiment <ArrowUpRight size={15} />
          </Link>
        }
      />
      <div className="metrics">
        {[
          ["Samples", fmt(row.data.rows, 0)],
          ["Duration", timeLabel(row.data.duration_s)],
          ["Sampling rate", `${fmt(row.data.sample_rate_hz, 1)} Hz`],
          ["GPS fixes", fmt(row.data.reference_samples, 0)],
        ].map(([label, value]) => (
          <div className="metric" key={label}>
            <div>{label}</div>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <section className="panel">
        <div className="panel-heading">
          <h2>Recorded reference route</h2>
          <span className="soft-tag">GPS observations</span>
        </div>
        {row.data.reference_samples ? (
          <ResearchMap paths={paths} />
        ) : (
          <Empty title="No GPS reference">
            <p>
              Provide explicit initial conditions to estimate position. Accuracy
              cannot be measured without a reference.
            </p>
          </Empty>
        )}
      </section>
      <section className="panel analysis-panel">
        <div className="panel-heading">
          <h2>Accelerometer · m/s²</h2>
        </div>
        <div className="analysis-chart">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={samples.data}>
              <CartesianGrid strokeDasharray="3 5" />
              <XAxis dataKey="t" tickFormatter={timeLabel} />
              <YAxis />
              <Tooltip />
              <Legend />
              {["ax", "ay", "az"].map((k, i) => (
                <Line
                  key={k}
                  dataKey={k}
                  stroke={["#407654", "#c28564", "#a79853"][i]}
                  dot={false}
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>
      <div className="dashboard-columns">
        <section className="panel form-panel">
          <h2>Data quality & provenance</h2>
          {row.data.warnings.map((w: string) => (
            <p className="quality-note" key={w}>
              <AlertCircle size={15} />
              {w}
            </p>
          ))}
          <dl className="metadata">
            <dt>Source</dt>
            <dd>{row.data.source}</dd>
            <dt>SHA256</dt>
            <dd className="checksum">{row.data.checksum}</dd>
            <dt>Selected segment</dt>
            <dd>
              {row.data.segment == null
                ? "Entire recording"
                : Number(row.data.segment) + 1}
            </dd>
            <dt>Preprocessing</dt>
            <dd>Adapter v{row.data.adapter_version} · raw source preserved</dd>
          </dl>
        </section>
        <section className="panel form-panel">
          <h2>Save stationary calibration</h2>
          <p className="helper-text">
            Choose at least three seconds with the phone still in its mount.
            Moving segments are rejected.
          </p>
          <form onSubmit={calibrate}>
            <Field label="Profile name">
              <input
                required
                name="name"
                defaultValue="Stationary mount"
                maxLength={120}
              />
            </Field>
            <div className="form-grid">
              <Field label="Start (seconds)">
                <input
                  name="start"
                  type="number"
                  min="0"
                  step="0.1"
                  defaultValue="0"
                  required
                />
              </Field>
              <Field label="End (seconds)">
                <input
                  name="end"
                  type="number"
                  min="3"
                  max={row.data.duration_s}
                  step="0.1"
                  defaultValue="5"
                  required
                />
              </Field>
            </div>
            {error && <Notice>{error}</Notice>}
            {saved && <p className="success-message">Saved {saved}</p>}
            <button className="button" disabled={busy}>
              {busy ? "Checking…" : "Validate & save calibration"}
            </button>
          </form>
        </section>
      </div>
    </>
  );
}
