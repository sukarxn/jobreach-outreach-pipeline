import { Switch, Route } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Dashboard from "./pages/Dashboard";
import Jobs from "./pages/Jobs";
import Runs from "./pages/Runs";
import Setup from "./pages/Setup";
import Layout from "./components/Layout";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Layout>
        <Switch>
          <Route path="/" component={Dashboard} />
          <Route path="/jobs" component={Jobs} />
          <Route path="/runs" component={Runs} />
          <Route path="/setup" component={Setup} />
        </Switch>
      </Layout>
    </QueryClientProvider>
  );
}
