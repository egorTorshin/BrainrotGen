import { useState } from "react";
import Generate from "./pages/Generate";
import Preview from "./pages/Preview";

function App() {
    const [jobId, setJobId] = useState<string | null>(null);

    if (!jobId) {
        return (
            <Generate onCreated={setJobId} />
        );
    }

    return <Preview jobId={jobId} onBack={() => setJobId(null)} />
}

export default App;