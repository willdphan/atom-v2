import fs from "fs/promises";
import type { NextApiRequest, NextApiResponse } from "next";

export default async function clearTranscript(
  req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    await fs.writeFile("pages/api/transcript.txt", "");
    res.status(200).end();
  } catch (error) {
    console.error(error);
    res.status(500).end();
  }
}
