import Cors from "cors";
import type { NextApiRequest, NextApiResponse } from "next";

// Initializing the cors middleware
// You can read more about the available options here: https://github.com/expressjs/cors#configuration-options
const whitelist = ["http://localhost:3000", "https://hoppscotch.io"];
const allowedOrigins = (origin: string = "", callback: Function) => {
  if (whitelist.indexOf(origin) !== -1) {
    callback(null, true);
  } else {
    callback(new Error("Not allowed by CORS"));
  }
};
const cors = Cors({
  methods: ["POST", "GET", "HEAD", "OPTIONS"],
  origin: allowedOrigins,
  credentials: true,
});

// Helper method to wait for a middleware to execute before continuing
// And to throw an error when an error happens in a middleware
function runMiddleware(
  req: NextApiRequest,
  res: NextApiResponse,
  fn: Function
) {
  return new Promise((resolve, reject) => {
    fn(req, res, (result: any) => {
      if (result instanceof Error) {
        return reject(result);
      }

      return resolve(result);
    });
  });
}

const enableCors =
  (fn: Function) => async (req: NextApiRequest, res: NextApiResponse) => {
    // Run the middleware
    await runMiddleware(req, res, cors);

    if (req.method === "OPTIONS") {
      res.status(200).end();
      return;
    }

    // res.setHeader('Access-Control-Allow-Credentials', true)
    // res.setHeader('Access-Control-Allow-Origin', '*') // replace this your actual origin
    // res.setHeader('Access-Control-Allow-Methods', 'GET,DELETE,PATCH,POST,PUT')
    // res.setHeader(
    //   'Access-Control-Allow-Headers',
    //   'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
    // )

    return await fn(req, res);
  };

export default enableCors;
