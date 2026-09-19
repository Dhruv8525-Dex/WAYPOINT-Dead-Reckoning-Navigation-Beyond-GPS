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
export default function Experiments() {
  const { project } = useWorkspace();
  const records = useRecords();
  const datasets = records.data.filter((r) => r.kind === "dataset"),
    models = records.data.filter((r) => r.kind === "model"),
    calibrations = records.data.filter((r) => r.kind === "calibration");
  const jobs = useResource<Job[]>(
    project ? `/jobs?project_id=${project.id}` : null,
    [],
    2000,
  );
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [selected, setSelected] = useState(
      new URLSearchParams(location.search).get("dataset") || "",
    );
  const current = datasets.find((d) => d.id === selected) || datasets[0];
  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    setBusy(true);
    try {
      const config: any = {
        project_id: project!.id,
        dataset_id: current.id,
        name: data.get("name"),
        outages: data.get("outage")
          ? [{ start: Number(data.get("start")), end: Number(data.get("end")) }]
          : [],
        model_id: data.get("model") || null,
        calibration_id: data.get("calibration") || null,
        accel_noise: Number(data.get("accel_noise")),
        gyro_noise: Number(data.get("gyro_noise")),
        gps_noise: Number(data.get("gps_noise")),
        mount_yaw_deg: Number(data.get("mount")),
      };
      for (const key of [
        "initial_heading_deg",
        "initial_speed_mps",
        "initial_lat",
        "initial_lng",
      ])
        if (data.get(key) !== "") config[key] = Number(data.get(key));
      await post("/runs", config);
      jobs.refresh();
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
        title="Experiments"
        description="Create a real GPS outage. Compare estimators against the withheld reference."
      />
      <ProjectRequired>
        {!datasets.length ? (
          <Empty title="A recording comes first">
            <Link className="button" to="/app/import">
              Import a recording
            </Link>
          </Empty>
        ) : (
          <section className="panel form-panel">
            <h2>Configure an experiment</h2>
            <form onSubmit={submit}>
              <div className="form-grid">
                <Field label="Experiment name">
                  <input
                    name="name"
                    defaultValue="GPS outage study"
                    required
                    maxLength={120}
                  />
                </Field>
                <Field label="Recording">
                  <select
                    value={current?.id || ""}
                    onChange={(e) => setSelected(e.target.value)}
                  >
                    {datasets.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Learned velocity model">
                  <select name="model">
                    <option value="">Classical estimators only</option>
                    {models.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Calibration profile">
                  <select name="calibration">
                    <option value="">
                      Recorded gravity / stationary start
                    </option>
                    {calibrations.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>
              <div className="outage-config">
                <label className="check-field">
                  <input type="checkbox" name="outage" defaultChecked />
                  Withhold GPS measurements during an outage
                </label>
                <div className="form-grid">
                  <Field label="Outage start (seconds)">
                    <input
                      name="start"
                      type="number"
                      min="0"
                      step="0.1"
                      defaultValue="30"
                      required
                    />
                  </Field>
                  <Field label="Outage end (seconds)">
                    <input
                      name="end"
                      type="number"
                      min="0.1"
                      step="0.1"
                      max={current?.data.duration_s}
                      defaultValue="60"
                      required
                    />
                  </Field>
                </div>
                <small>
                  The reference is used only to score errors. It is not
                  available to estimators during this interval.
                </small>
              </div>
              <details className="advanced">
                <summary>Sensor noise & initialization</summary>
                <div className="form-grid">
                  {[
                    [
                      "accel_noise",
                      "Accelerometer noise",
                      "0.3",
                      "0.001",
                      "10",
                    ],
                    ["gyro_noise", "Gyroscope noise", "0.02", "0.0001", "1"],
                    ["gps_noise", "GPS position noise (m)", "5", "0.1", "100"],
                    [
                      "mount",
                      "Mount yaw correction (degrees)",
                      "0",
                      "-180",
                      "180",
                    ],
                  ].map(([key, label, value, min, max]) => (
                    <Field key={key} label={label}>
                      <input
                        name={key}
                        type="number"
                        step="any"
                        defaultValue={value}
                        min={min}
                        max={max}
                        required
                      />
                    </Field>
                  ))}
                  {[
                    ["initial_heading_deg", "Initial heading (degrees)"],
                    ["initial_speed_mps", "Initial speed (m/s)"],
                    ["initial_lat", "Initial latitude"],
                    ["initial_lng", "Initial longitude"],
                  ].map(([key, label]) => (
                    <Field
                      key={key}
                      label={label}
                      hint="Leave blank to use the first available GPS fix."
                    >
                      <input name={key} type="number" step="any" />
                    </Field>
                  ))}
                </div>
              </details>
              {error && <Notice>{error}</Notice>}
              <button className="button primary" disabled={busy}>
                {busy ? "Queuing…" : "Run experiment"}
                <Play size={15} />
              </button>
            </form>
          </section>
        )}
        <Jobs items={jobs.data} refresh={jobs.refresh} />
        <section className="panel">
          <div className="panel-heading">
            <h2>Saved results</h2>
          </div>
          {records.data
            .filter((r) => r.kind === "run")
            .map((r) => (
              <Link className="list-row" to={`/app/runs/${r.id}`} key={r.id}>
                <Activity size={19} />
                <span>
                  <strong>{r.name}</strong>
                  <small>
                    {r.data.dataset_name} · {r.data.metric_scope}
                  </small>
                </span>
                <ArrowUpRight size={16} />
              </Link>
            ))}
        </section>
      </ProjectRequired>
    </>
  );
}
