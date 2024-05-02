import { GetObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { Upload } from "@aws-sdk/lib-storage";
import { Readable } from "stream";
import { parse, stringify } from "csv";

export default async function handler(req, res) {
  if (req.method === "POST") {
    const { name, email } = req.body;
    // console.log(`Name: ${name}, Email: ${email}`);

    const client = new S3Client({ region: "us-east-2" });

    const bucket = "coming-soon-orijbjk9x8yg8fonwz1usjtx53jowuse2a-s3alias";

    const getObjectParams = {
      Bucket: bucket,
      Key: "submissions.csv",
    };

    try {
      // Check if "submissions.csv" exists
      await client.send(new GetObjectCommand(getObjectParams));
    } catch (error) {
      // If the file doesn't exist, create it with first submission
      const initialData = stringify([{ Name: name, Email: email }], {
        columns: ["Name", "Email"],
      });
      const initialPutParams = {
        Bucket: bucket,
        Key: "submissions.csv",
        Body: initialData,
      };

      const upload = new Upload({
        client: client,
        params: initialPutParams,
      });

      await upload.done();

      return res
        .status(200)
        .json({ message: "Form submitted and file created." });
    }

    // File exists, append new submission
    // Fetch existing data
    const getResponse = await client.send(
      new GetObjectCommand(getObjectParams)
    );
    const data = await new Promise((resolve, reject) => {
      const chunks = [];
      getResponse.Body.on("data", (chunk) => chunks.push(chunk));
      getResponse.Body.on("error", reject);
      getResponse.Body.on("end", () =>
        resolve(Buffer.concat(chunks).toString("utf8"))
      );
    });

    // Parse existing records
    const records = await new Promise((resolve, reject) => {
      const chunks = [];
      parse(data, { delimiter: "," })
        .on("data", (chunk) => chunks.push(chunk))
        .on("error", reject)
        .on("end", () => resolve(chunks));
    });

    // Append new submission
    records.push({ Name: name, Email: email });

    // Prepare updated data
    const newData = stringify(records, {
      columns: ["Name", "Email"],
    });

    // Upload updated data to S3
    const upload = new Upload({
      client: client,
      params: {
        Bucket: bucket,
        Key: "submissions.csv",
        Body: newData,
      },
    });

    await upload.done();

    return res
      .status(200)
      .json({ message: "Form submitted and file updated." });
  } else {
    return res.status(405).json({ message: "Method not allowed." });
  }
}
