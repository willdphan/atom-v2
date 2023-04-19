import { NextApiRequest, NextApiResponse } from "next";
import { spawn } from "child_process";
import { promisify } from "util";
import fs from "fs/promises";

const runScript = promisify(
  (
    scriptPath: string,
    callback: (err: Error | null, result: string | null) => void
  ) => {
    const child = spawn("python", [scriptPath]);

    child.stderr.on("data", (data) => {
      console.error(`stderr: ${data}`);
    });

    child.on("close", async (code) => {
      if (code !== 0) {
        console.error(`Python script exited with code ${code}`);
        callback(new Error(`Python script exited with code ${code}`), null);
      } else {
        try {
          const transcript = await fs.readFile(
            "pages/api/transcript.txt",
            "utf-8"
          );
          console.log(`Transcript: ${transcript}`);
          callback(null, transcript);
        } catch (err) {
          console.error("Error reading transcript file:", err);
          callback(err, null);
        }
      }
    });
  }
);

const readFile = async (filePath) => {
  try {
    const data = await fs.readFile(filePath, "utf-8");
    return data;
  } catch (err) {
    console.error("Error reading file:", err);
    return null;
  }
};

export default async (req: NextApiRequest, res: NextApiResponse) => {
  if (req.method === "POST") {
    res.status(405).json({ message: "Method not allowed" });
  } else if (req.method === "GET") {
    const transcript = await readFile("pages/api/transcript.txt");

    if (transcript) {
      res.status(200).send(transcript);
    } else {
      res.status(200).send(""); // Return an empty string when transcript is empty
    }
  } else {
    res.status(405).json({ message: "Method not allowed" });
  }
};

export const config = {
  api: {
    bodyParser: {
      sizeLimit: "10mb",
    },
  },
};

runScript("pages/api/atom.py");
