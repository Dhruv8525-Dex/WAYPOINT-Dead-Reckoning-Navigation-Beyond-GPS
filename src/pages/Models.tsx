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
export default function Models() {
  const { project } = useWorkspace();
  const records = useRecords();
  const datasets = records.data.filter((r) => r.kind === "dataset");
  const jobs = useResource<Job[]>(
    project ? `/jobs?project_id=${project.id}` : null,
    [],
    3000,
  );
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const train = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    setBusy(true);
    try {
      await post("/training", {
        project_id: project!.id,
        name: data.get("name"),
        architecture: data.get("architecture"),
        train_ids: [data.get("train")],
        validation_ids: [data.get("validation")],
        test_ids: [data.get("test")],
        epochs: Number(data.get("epochs")),
        seed: 42,
      });
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
        title="Velocity models"
        description="Train on one recording. Validate on another. Test on an untouched third."
      />
      <ProjectRequired>
        <section className="panel form-panel">
          <h2>Train a model</h2>
          <p className="helper-text">
            Five-second causal IMU windows, 10 Hz processing, and GPS speed as
            the training label. Inference never reads GPS speed.
          </p>
          {datasets.length < 3 ? (
            <Notice>
              Import at least three independent recordings before training. Do
              not split overlapping windows across train and test sets.
            </Notice>
          ) : (
            <form onSubmit={train}>
              <div className="form-grid">
                <Field label="Model name">
                  <input
                    name="name"
                    required
                    defaultValue="Velocity research model"
                    maxLength={120}
                  />
                </Field>
                <Field label="Architecture">
                  <select name="architecture">
                    <option value="ridge">
                      Ridge regression · explainable baseline
                    </option>
                    <option value="cnn_gru">
                      Causal CNN–GRU · learned velocity
                    </option>
                  </select>
                </Field>
                {["train", "validation", "test"].map((split, i) => (
                  <Field
                    key={split}
                    label={`${split[0].toUpperCase() + split.slice(1)} recording`}
                  >
                    <select name={split} defaultValue={datasets[i]?.id}>
                      {datasets.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                    </select>
                  </Field>
                ))}
                <Field
                  label="Maximum neural epochs"
                  hint="Early stopping uses validation error; test data never selects the model."
                >
                  <input
                    name="epochs"
                    type="number"
                    min="1"
                    max="200"
                    defaultValue="20"
                    required
                  />
                </Field>
              </div>
              {error && <Notice>{error}</Notice>}
              <button className="button primary" disabled={busy}>
                {busy ? "Queuing…" : "Start training"}
                <FlaskConical size={15} />
              </button>
            </form>
          )}
        </section>
        <div className="model-grid">
          {records.data
            .filter((r) => r.kind === "model")
            .map((r) => (
              <section className="panel form-panel" key={r.id}>
                <div className="section-title">
                  <h2>{r.name}</h2>
                  <Status value="completed" />
                </div>
                <p className="helper-text">
                  {r.data.architecture} ·{" "}
                  {r.data.training_samples.toLocaleString()} training windows ·{" "}
                  {r.data.device}
                </p>
                <div className="model-metrics">
                  <div>
                    <span>Held-out test RMSE</span>
                    <strong>
                      {fmt(r.data.test.rmse_mps)} <small>m/s</small>
                    </strong>
                  </div>
                  <div>
                    <span>Validation RMSE</span>
                    <strong>
                      {fmt(r.data.validation.rmse_mps)} <small>m/s</small>
                    </strong>
                  </div>
                </div>
                <p className="helper-text">
                  Measured inference: {fmt(r.data.inference_ms_per_window, 3)}{" "}
                  ms/window. Training: {fmt(r.data.runtime_s)} seconds.
                </p>
                <details className="advanced">
                  <summary>Training history & split provenance</summary>
                  <pre>
                    {JSON.stringify(
                      {
                        history: r.data.history,
                        splits: r.data.config,
                        checksums: r.data.checksums,
                      },
                      null,
                      2,
                    )}
                  </pre>
                </details>
                <Link className="button" to="/app/experiments">
                  Use in an experiment <ArrowRight size={15} />
                </Link>
              </section>
            ))}
        </div>
        <Jobs
          items={jobs.data.filter((j) => j.kind === "training")}
          refresh={jobs.refresh}
        />
      </ProjectRequired>
    </>
  );
}
