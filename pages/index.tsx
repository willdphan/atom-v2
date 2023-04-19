import React, { useEffect, useState } from "react";
import Image from "next/image";
import blue from "public/blue3.gif";

export default function Home() {
  const introText =
    "Hello, I am ATOM, your AI executive assistant. How can I help you today?";
  const [displayedMessage, setDisplayedMessage] = useState(introText);

  useEffect(() => {
    const fetchAndUpdateTranscript = async () => {
      try {
        const response = await fetch("/api/listen");
        const text = await response.text();
        console.log("Transcript:", text);

        if (!text) {
          setTimeout(fetchAndUpdateTranscript, 1);
          return;
        }

        const lines = text.split("\n");

        let messages = "";

        for (let i = 0; i < lines.length; i += 3) {
          messages += lines.slice(i, i + 3).join("\n") + "\n";
        }

        if (messages !== "") {
          setDisplayedMessage(messages);
        }
      } catch (err) {
        console.error(err);
      }

      setTimeout(fetchAndUpdateTranscript, 1);
    };

    const clearTranscript = async () => {
      await fetch("/api/clearTranscript");
    };

    clearTranscript();
    setTimeout(fetchAndUpdateTranscript, 0);
  }, []);

  return (
    <div className="min-h-screen bg-[#000000] flex flex-col items-center justify-center ">
      <Image
        alt="image"
        className="rounded-xl w-[30em]"
        priority={true}
        src={blue}
        loading="eager"
        width={800}
        height={800}
      />
      <div className="leading-snug ">
        <pre className="font-roboto leading-10 font-[200] tracking-wider mt-[0em] mb-28 text-xl text-white  max-w-[15em] text-center overflow-hidden whitespace-pre-wrap line-clamp-3">
          {displayedMessage}
        </pre>
      </div>
    </div>
  );
}
