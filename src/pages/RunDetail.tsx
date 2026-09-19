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
export default function RunDetail() {
  const { id } = useParams();
  const record = useResource<RecordItem | null>(`/records/${id}`, null);
  const result = useResource<any>(`/runs/${id}/result`, null);
  const [index, setIndex] = useState(0),
    [playing, setPlaying] = useState(false),
    [visible, setVisible] = useState<Record<string, boolean>>({
      reference: true,
      inertial: true,
      ekf: true,
      ml: true,
    });
  const r = result.data;
  useEffect(() => {
    if (!playing || !r) return;
    const timer = setInterval(
      () =>
        setIndex((i) => {
          if (i >= r.time.length - 1) {
            setPlaying(false);
            return i;
          }
          return i + 1;
        }),
      100,
    );
    return () => clearInterval(timer);
  }, [playing, r]);
  const paths = useMemo(
    () => (r ? { reference: r.reference, ...r.series } : {}),
    [r],
  );
  const chart = useMemo(() => {
    if (!r) return [];
    const step = Math.max(1, Math.floor(r.time.length / 500));
    return r.time
      .map((t: number, i: number) => ({
        t,
        ...Object.fromEntries(
          Object.entries(r.series).map(([m, v]: any) => [m, v.error[i]]),
        ),
      }))
      .filter((_: any, i: number) => i % step === 0);
  }, [r]);
  if (result.error) return <Notice>{result.error}</Notice>;
  if (!r)
    return (
      <Empty title="Loading experiment">
        <p>Reading saved estimator outputs…</p>
      </Empty>
    );
  return (
    <>
      <Heading
        title={record.data?.name || "Experiment result"}
        description={`${record.data?.data.dataset_name || "Recording"} · immutable, reproducible result`}
        action={
          <div className="actions">
            <button
              className="button"
              onClick={() => downloadResource(`/runs/${id}/export?format=csv`, `waypoint-${id}.csv`)}
            >
              <Download size={15} />
              CSV
            </button>
            <button
              className="button"
              onClick={() => downloadResource(`/runs/${id}/export?format=json`, `waypoint-${id}.json`)}
            >
              JSON
            </button>
            <button
              className="button primary"
              onClick={() => downloadResource(`/runs/${id}/export?format=html`, `waypoint-${id}.html`)}
            >
              Report <ArrowUpRight size={15} />
            </button>
          </div>
        }
      />
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Trajectory explorer</h2>
            <p>
              {r.metric_scope} · {fmt(r.distance_m / 1000)} km reference
              distance
            </p>
          </div>
          <span
            className={`status ${r.outage[index] ? "status-running" : "status-completed"}`}
          >
            {r.outage[index] ? "GPS withheld" : "Outside configured outage"}
          </span>
        </div>
        <ResearchMap paths={paths} current={index} visible={visible} />
        <div className="map-legend">
          {Object.keys(paths).map((key) => (
            <button
              key={key}
              aria-pressed={visible[key]}
              onClick={() => setVisible({ ...visible, [key]: !visible[key] })}
            >
              <i style={{ background: methodColors[key] }} />
              {key === "ml" ? "Learned + EKF" : key}
            </button>
          ))}
        </div>
        <div className="playback">
          <button
            className="play-button"
            aria-label={playing ? "Pause playback" : "Play result"}
            onClick={() => {
              if (index >= r.time.length - 1) setIndex(0);
              setPlaying(!playing);
            }}
          >
            {playing ? <Pause size={15} /> : <Play size={15} />}
          </button>
          <span>{timeLabel(r.time[index])}</span>
          <input
            aria-label="Result playback position"
            type="range"
            min="0"
            max={r.time.length - 1}
            value={index}
            onChange={(e) => setIndex(Number(e.target.value))}
          />
          <span>{timeLabel(r.duration_s)}</span>
        </div>
      </section>
      <section className="panel analysis-panel">
        <div className="panel-heading">
          <h2>Position error · meters</h2>
          <span className="soft-tag">{r.metric_scope}</span>
        </div>
        <div className="analysis-chart">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chart}>
              <CartesianGrid strokeDasharray="3 5" vertical={false} />
              <XAxis dataKey="t" tickFormatter={timeLabel} minTickGap={50} />
              <YAxis width={60} />
              <Tooltip labelFormatter={(v) => `${v} seconds`} />
              <Legend />
              {Object.keys(r.series).map((key) => (
                <Line
                  key={key}
                  dataKey={key}
                  name={key === "ml" ? "Learned + EKF" : key}
                  stroke={methodColors[key]}
                  dot={false}
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>
      <section className="panel form-panel">
        <h2>Measured performance</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Method</th>
                <th>Position RMSE</th>
                <th>Endpoint drift</th>
                <th>Velocity RMSE</th>
                <th>Normalized drift</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(r.metrics).map(([key, m]: any) => (
                <tr key={key}>
                  <th>{key}</th>
                  <td>{fmt(m.position_rmse_m)} m</td>
                  <td>{fmt(m.endpoint_drift_m)} m</td>
                  <td>{fmt(m.velocity_rmse_mps)} m/s</td>
                  <td>{fmt(m.normalized_drift_percent)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="helper-text">
          Processing: {fmt(r.runtime_s)} s · {fmt(r.samples_per_second, 0)}{" "}
          samples/s · engine {r.engine_version}. Normalized endpoint drift uses
          total reference-route distance.
        </p>
        {r.notes.map((note: string) => (
          <p key={note} className="helper-text">
            {note}
          </p>
        ))}
        <details className="advanced">
          <summary>Experiment settings & provenance</summary>
          <pre>{JSON.stringify(r.config, null, 2)}</pre>
          <p className="checksum">Source SHA256: {r.dataset_checksum}</p>
        </details>
      </section>
    </>
  );
}
