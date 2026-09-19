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
export default function ImportPage() {
  const { project } = useWorkspace();
  const navigate = useNavigate();
  const [preview, setPreview] = useState<any>(null),
    [mapping, setMapping] = useState<Record<string, string>>({}),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const [name, setName] = useState(""),
    [timeUnit, setTimeUnit] = useState("s"),
    [gyroUnit, setGyroUnit] = useState("rad/s"),
    [segment, setSegment] = useState("");
  const upload = async (file: File) => {
    setBusy(true);
    setError("");
    setPreview(null);
    const data = new FormData();
    data.set("file", file);
    try {
      const result = await api("/uploads", { method: "POST", body: data });
      setPreview(result);
      setMapping(result.mapping);
      setName(file.name.replace(/\.[^.]+$/, ""));
      setTimeUnit(result.time_unit);
      setSegment(result.segments.length === 1 ? "0" : "");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const save = async () => {
    setBusy(true);
    try {
      const r = await post("/imports", {
        project_id: project!.id,
        upload_id: preview.upload_id,
        name,
        mapping: Object.fromEntries(
          Object.entries(mapping).filter(([, v]) => v),
        ),
        time_unit: timeUnit,
        gyro_unit: gyroUnit,
        segment: segment === "" ? null : Number(segment),
      });
      navigate(`/app/datasets/${r.id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <Heading
        title="Import a recording"
        description="Preview the source, map its columns, and check units before processing."
      />
      <ProjectRequired>
        <section className="panel form-panel">
          <div
            className="drop-zone"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (e.dataTransfer.files[0]) upload(e.dataTransfer.files[0]);
            }}
          >
            <Upload size={30} />
            <h2>Bring your motion data</h2>
            <p>IO-VNBD CSV, mapped CSV, or Waypoint JSON · maximum 128 MB</p>
            <label className="button">
              {busy ? "Reading file…" : "Choose a recording"}
              <input
                aria-label="Recording file"
                className="sr-only"
                type="file"
                accept=".csv,.json,.txt"
                disabled={busy}
                onChange={(e) => {
                  if (e.target.files?.[0]) upload(e.target.files[0]);
                }}
              />
            </label>
          </div>
          {error && <Notice>{error}</Notice>}
          {preview && (
            <>
              <div className="section-title">
                <h2>Review before import</h2>
                <span>{preview.rows.toLocaleString()} source rows</span>
              </div>
              <div className="form-grid">
                <Field label="Recording name">
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    maxLength={120}
                  />
                </Field>
                <Field label="Timestamp unit">
                  <select
                    value={timeUnit}
                    onChange={(e) => setTimeUnit(e.target.value)}
                  >
                    {["s", "ms", "ns"].map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </select>
                </Field>
                <Field label="Gyroscope unit">
                  <select
                    value={gyroUnit}
                    onChange={(e) => setGyroUnit(e.target.value)}
                  >
                    <option>rad/s</option>
                    <option>deg/s</option>
                  </select>
                </Field>
                <Field
                  label="Continuous segment"
                  hint="Timestamp resets separate trips. Raw files remain unchanged."
                >
                  <select
                    value={segment}
                    onChange={(e) => setSegment(e.target.value)}
                  >
                    <option value="">Choose a segment</option>
                    {preview.segments.map((s: any) => (
                      <option value={s.index} key={s.index}>
                        Segment {s.index + 1} · {s.rows.toLocaleString()} rows
                      </option>
                    ))}
                  </select>
                </Field>
              </div>
              <div className="mapping-grid">
                {[
                  "t",
                  "ax",
                  "ay",
                  "az",
                  "gx",
                  "gy",
                  "gz",
                  "lat",
                  "lng",
                  "speed",
                  "heading",
                  "accuracy",
                  "gravity_x",
                  "gravity_y",
                  "gravity_z",
                ].map((key, i) => (
                  <Field key={key} label={`${key}${i < 7 ? " *" : ""}`}>
                    <select
                      value={mapping[key] || ""}
                      onChange={(e) =>
                        setMapping({ ...mapping, [key]: e.target.value })
                      }
                    >
                      <option value="">
                        {i < 7 ? "Select required column" : "Not provided"}
                      </option>
                      {preview.columns.map((column: string) => (
                        <option key={column}>{column}</option>
                      ))}
                    </select>
                  </Field>
                ))}
              </div>
              <p className="helper-text">
                Acceleration uses m/s². Generic speed uses m/s; IO-VNBD GPS
                SPEED is converted from km/h. Heading uses degrees clockwise
                from north. GPS reference remains separate from IMU inputs.
              </p>
              <button
                className="button primary"
                disabled={busy || !name.trim() || segment === ""}
                onClick={save}
              >
                {busy ? "Validating…" : "Validate & save recording"}
                <Check size={16} />
              </button>
            </>
          )}
        </section>
      </ProjectRequired>
    </>
  );
}
