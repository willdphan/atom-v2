/*global chrome*/

import "../styles/globals.css";
import * as React from "react";
import "regenerator-runtime/runtime";

export default function App({ Component, pageProps }) {
  return <Component {...pageProps} />;
}
