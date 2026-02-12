export type RecapRequest = {
  repo: string;
  since: string;
  until: string;
  githubToken?: string;
};

export type RecapResponse = {
  project: {
    repo: string;
    title: string;
  };
  range: {
    since: string;
    until: string;
  };
  summary: {
    headline: string;
    highlights: string[];
    risks: string[];
    next: string[];
  };
  chapters: {
    title: string;
    beats: string[];
  }[];
  timeline: {
    date: string;
    title: string;
    detail: string;
    type: "pr" | "commit" | "note";
  }[];
  metrics: {
    prCount: number;
    commitCount: number;
    noteCount: number;
  };
  sourceNotes: string[];
};
