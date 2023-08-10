import Cors from "cors";
import { exec } from "child_process";
import enableCors from "../../src/utils/enableCors";
import type { NextApiRequest, NextApiResponse } from "next";

const handler = (req: NextApiRequest, res: NextApiResponse) => {
  if (req.method === "POST") {
    if (!req.complete) {
      res.status(400).json({ message: "Request incomplete" });
      return;
    }
    const host = "127.0.0.1";
    const port = req.body?.port || "8000";
    console.log("@@ Starting inference server on", port);

    // Start the inference server
    // exec(`npm run fastapi-dev:start --host=127.0.0.1 --port=${port}`);
    // @TODO Determine if this is already running. Could set a state var in GUI that prevents another startup pressed.
    const { stdout, stderr, pid } = exec(
      `python -m uvicorn api.index:app --host ${host} --port ${port} --reload`
    );
    // check running process on port `lsof -i :8000`
    // nestat -aon | findstr 123456
    if (stderr?.errored) {
      console.error("@@ Error starting inference server", stderr);
      res.status(400).json({
        message: `Something went wrong. Failed to start inference server on port ${port}`,
      });
    } else {
      res.status(200).json({
        message: `Started inference server on port ${port}`,
        pid: pid,
      });
    }
  } else {
    // Not allowed
    res.status(400).json({ message: "Method not allowed" });
  }
};

module.exports = enableCors(handler);
