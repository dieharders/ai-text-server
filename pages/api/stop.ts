import enableCors from "../../src/utils/enableCors";
import { exec } from "child_process";
import type { NextApiRequest, NextApiResponse } from "next";

// @TODO May be able to do this by callin shutdown() from the server instance OR `os.kill(pid, signal.SIGKILL)` from Python
const handler = (req: NextApiRequest, res: NextApiResponse) => {
  if (req.method === "POST") {
    if (!req.complete) {
      res.status(400).json({ message: "Request incomplete" });
      return;
    }
    const pid = req.body?.pid;
    if (!pid) {
      res.status(400).json({ message: "No param 'pid' passed." });
      return;
    }
    // const { stdout, stderr } = exec(`bash kill -9 ${pid}`);
    const { stdout, stderr } = exec(`taskkill /F /PID ${pid}`);
    if (stderr?.errored) {
      res.status(400).json({ message: "Error,", stderr });
      console.log("@@ Error stopping inference server", stderr);
    } else {
      console.log("@@ Success, inference shutdown");
      res.status(200).json({ message: `Inference server [${pid}] shutdown.` });
    }
  } else {
    // Not allowed
    res.status(400).json({ message: "Method not allowed" });
  }
};

module.exports = enableCors(handler);
