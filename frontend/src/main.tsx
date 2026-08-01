// Amplify の configure は副作用 import で行う。他の import より先に評価される
// 必要があるため最先頭に置く（順序 load-bearing）。
import "./auth/amplify-config";
// Hub listener は Amplify.configure() の後に登録する必要があるので直後に置く。
import "./auth/auth-hub-listener";

import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";

const queryClient = new QueryClient();
const theme = createTheme({
  palette: { primary: { main: "#3949ab" } },
  typography: { fontFamily: '"Helvetica Neue", Arial, "Hiragino Sans", sans-serif' },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
