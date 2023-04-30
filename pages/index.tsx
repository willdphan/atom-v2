import React, { useEffect, useState } from "react";
import Image from "next/image";
import blue from "public/blue3.gif";
import siri from "public/siri.gif";

const Loader = () => {
  return (
    <div className="flex justify-center">
      <span className="circle animate-loader"></span>
      <span className="circle animate-loader animation-delay-200"></span>
      <span className="circle animate-loader animation-delay-400"></span>
    </div>
  );
};

export default function Home() {
  const introText =
    "Hello, I'm ATOM, your AI executive assistant. How can I help you today?";
  const [displayedMessage, setDisplayedMessage] = useState(introText);
  const [loading, setLoading] = useState(false);
  const [lastUpdateTime, setLastUpdateTime] = useState(Date.now());

  useEffect(() => {
    const fetchAndUpdateTranscript = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/api/listen?timestamp=${lastUpdateTime}`);
        const text = await response.text();
        console.log("Transcript:", text);

        if (!text) {
          setLoading(false);
          setTimeout(fetchAndUpdateTranscript, 1000);
          return;
        }

        const lines = text.split("\n");

        let messages = "";

        for (let i = 0; i < lines.length; i += 3) {
          messages += lines.slice(i, i + 3).join("\n") + "\n";
        }

        if (messages !== "") {
          setDisplayedMessage(messages);
          setLastUpdateTime(Date.now());
        }
      } catch (err) {
        console.error(err);
      }

      setLoading(false);
      setTimeout(fetchAndUpdateTranscript, 1000);
    };

    const clearTranscript = async () => {
      await fetch("/api/clearTranscript");
    };

    clearTranscript();
    fetchAndUpdateTranscript();
  }, []);

  return (
    <div className="min-h-screen bg-[#000000] flex flex-col items-center justify-center ">
      <Image
        alt="image"
        className="rounded-xl w-[20em] mt-10 mb-14"
        priority={true}
        src={siri}
        loading="eager"
        width={900}
        height={900}
      />
      <div className="leading-snug ease-in-out">
      <pre className="font-roboto leading-10 font-[100] tracking-wider mt-[0em] mb-28 text-xl text-white max-w-[14em] text-center overflow-hidden whitespace-pre-wrap line-clamp-3 ">
      {displayedMessage}
</pre>
      </div>
      {loading ? <Loader /> : null}
    </div>
  );
}
