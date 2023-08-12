import type { NextApiRequest, NextApiResponse } from "next";
import enableCors from "../../src/utils/enableCors";

const handler = (req: NextApiRequest, res: NextApiResponse) => {
  if (req.method === "GET") {
    // Incomplete
    if (!req.complete) {
      res.status(400).json({ message: "Request incomplete", success: true });
      return;
    }
    // Success
    console.log("@@ Starting api server");
    res.status(200).json({
      message: `Connected to api server.`,
      success: true,
    });
  } else {
    // Not allowed
    res.status(400).json({ message: "Method not allowed", success: false });
  }
};

module.exports = enableCors(handler);
