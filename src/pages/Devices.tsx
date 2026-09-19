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
export default function Devices() {
  const { project } = useWorkspace();
  const devices = useResource<any[]>("/devices", [], 4000);
  const recordings = useResource<any[]>("/recordings", [], 2000);
  const [pair, setPair] = useState<any>(null),
    [error, setError] = useState(""),
    [message, setMessage] = useState("");
  const act = async (fn: () => Promise<any>) => {
    try {
      await fn();
      setError("");
      devices.refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  };
  return (
    <>
      <Heading
        title="Phone recorder"
        description="Capture motion on Android. Keep recording through signal and network loss."
        action={
          <button className="button primary" onClick={() => downloadResource('/android/apk', 'waypoint-recorder.apk')}>
            <Download size={15} />
            Download Android APK
          </button>
        }
      />
      {error && <Notice>{error}</Notice>}
      {message && <p className="success-message">{message}</p>}
      <div className="dashboard-columns">
        <section className="panel form-panel">
          <h2>Pair your Android phone</h2>
          <ol className="instructions">
            <li>
              Install the local APK and grant sensor/location permissions.
            </li>
            <li>
              Connect the phone and computer to the same network. Start the
              backend with LAN mode enabled.
            </li>
            <li>
              Enter the computer’s LAN address, pairing code, and certificate
              fingerprint in the recorder.
            </li>
          </ol>
          <button
            className="button"
            onClick={() => act(async () => setPair(await post("/pairing", {})))}
          >
            Generate pairing code <Plus size={15} />
          </button>
          {pair && (
            <div className="pairing-details">
              <span className="tiny-label">
                ONE-TIME CODE · EXPIRES IN FIVE MINUTES
              </span>
              <strong>{pair.code}</strong>
              <Field label="Certificate SHA256">
                <textarea readOnly value={pair.certificate_sha256} />
              </Field>
              <p className="helper-text">
                Server address: https://YOUR-COMPUTER-IP:{pair.port}. The
                certificate must match exactly; never bypass verification.
              </p>
            </div>
          )}
        </section>
        <section className="panel">
          <div className="panel-heading">
            <h2>Paired devices</h2>
          </div>
          {devices.data.map((d) => (
            <div className="list-row" key={d.id}>
              <Smartphone size={21} />
              <span>
                <strong>{d.name}</strong>
                <small>{d.revoked ? "Revoked" : "Authorized recorder"}</small>
              </span>
              {!d.revoked && (
                <button
                  className="button"
                  onClick={() => act(() => post(`/devices/${d.id}/revoke`, {}))}
                >
                  Revoke
                </button>
              )}
            </div>
          ))}
          {!devices.data.length && (
            <Empty title="No paired phones">
              <p>
                Recording works offline. Pair when ready to transfer or stream.
              </p>
            </Empty>
          )}
        </section>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Received recordings</h2>
            <p>Acknowledged batches are stored before transfer succeeds.</p>
          </div>
          <span className="soft-tag">
            <Radio size={12} />
            Live receiver
          </span>
        </div>
        {recordings.data.map((r) => (
          <div className="recording-row" key={`${r.device_id}:${r.session_id}`}>
            <div>
              <strong>{r.session_id}</strong>
              <p>
                {r.samples.toLocaleString()} samples · {r.batches} batches ·
                last timestamp {fmt(r.last_sample.t)} s
              </p>
              <small>
                Acceleration {fmt(r.last_sample.ax)} / {fmt(r.last_sample.ay)} /{" "}
                {fmt(r.last_sample.az)} m/s²
              </small>
            </div>
            <button
              className="button"
              disabled={!project}
              onClick={() =>
                act(async () => {
                  await post(
                    `/recordings/${r.device_id}/${r.session_id}/import?project_id=${project!.id}`,
                    {
                      name: `Phone recording ${r.session_id}`,
                      description: "",
                    },
                  );
                  setMessage(
                    "Recording imported. Open the recording library to inspect it.",
                  );
                })
              }
            >
              Import to project <ArrowRight size={15} />
            </button>
          </div>
        ))}
        {!recordings.data.length && (
          <p className="helper-text padded">
            No batches received yet. Start recording on your phone, then upload
            or enable live transfer.
          </p>
        )}
      </section>
    </>
  );
}
