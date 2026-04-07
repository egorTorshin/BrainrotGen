type CreateJobRequest = {
  text: string;
  voice: string;
  background: string;
};

type CreateJobResponse = {
  job_id: string;
};


export async function createJob(_data: CreateJobRequest): Promise<CreateJobResponse> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ job_id: "123" });
    }, 500);
  })
}

export async function getStatus(_jobId: string): Promise<{
  status: "pending" | "processing" | "done" | "failed";
  url?: string;
}> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ status: "done", url: "https://www.w3schools.com/html/mov_bbb.mp4" });
    }, 500);
  });
}