import {lazy,Suspense} from "react";
import {BrowserRouter,Routes,Route,Link} from "react-router-dom";
import {Empty} from "./ui";
import "./product.css";
const Layout = lazy(() => import("./pages/Layout"));
const Landing = lazy(() => import("./pages/Landing"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Projects = lazy(() => import("./pages/Projects"));
const Datasets = lazy(() => import("./pages/Datasets"));
const ImportPage = lazy(() => import("./pages/ImportPage"));
const DatasetDetail = lazy(() => import("./pages/DatasetDetail"));
const Experiments = lazy(() => import("./pages/Experiments"));
const RunDetail = lazy(() => import("./pages/RunDetail"));
const Models = lazy(() => import("./pages/Models"));
const Devices = lazy(() => import("./pages/Devices"));
const Documentation = lazy(() => import("./pages/Documentation"));
const SettingsPage = lazy(() => import("./pages/SettingsPage"));
export default function App() {
  return (
    <BrowserRouter><Suspense fallback={<Empty title="Opening page"><p>Loading workspace tools…</p></Empty>}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="projects" element={<Projects />} />
          <Route path="datasets" element={<Datasets />} />
          <Route path="datasets/:id" element={<DatasetDetail />} />
          <Route path="import" element={<ImportPage />} />
          <Route path="experiments" element={<Experiments />} />
          <Route path="runs/:id" element={<RunDetail />} />
          <Route path="models" element={<Models />} />
          <Route path="devices" element={<Devices />} />
          <Route path="docs" element={<Documentation />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        <Route
          path="*"
          element={
            <Empty title="This page does not exist">
              <Link className="button" to="/app">
                Return to workspace
              </Link>
            </Empty>
          }
        />
      </Routes>
    </Suspense></BrowserRouter>
  );
}
