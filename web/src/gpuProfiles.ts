import type { GpuType } from './gpuPrices';

export const GPU_PROFILE_REVIEWED = '2026-09-14';
export const GPU_SUPPORT_SOURCE = 'https://docs.nvidia.com/datacenter/tesla/drivers/cuda-toolkit-driver-and-architecture-matrix.html';
export interface GpuProfile {
  architecture: string; introduced: string; category: string; summary: string;
  uses: string[]; availability: string; source: string;
}
export const GPU_PROFILES: Record<GpuType, GpuProfile> = {
  'A100 SXM4': {
    architecture: 'Ampere', introduced: '2020-05-14', category: 'Data center GPU',
    summary: 'An earlier generation of NVIDIA server GPU built for AI and scientific computing. The Ornn series tracks the SXM4 model.',
    uses: ['Training AI models', 'Running AI models (inference)', 'Data analysis and scientific computing'],
    availability: 'NVIDIA announced the A100 in May 2020 and said it was already shipping. The year describes the model family; the manufacture date of a rented unit is unknown.',
    source: 'https://nvidianews.nvidia.com/news/nvidias-new-ampere-data-center-gpu-in-full-production',
  },
  'H100 SXM': {
    architecture: 'Hopper', introduced: '2022-03-22', category: 'Data center GPU',
    summary: 'A server GPU designed for large AI workloads. Its Transformer Engine accelerates the calculations used by large language models.',
    uses: ['Training large language models', 'AI inference and recommendation systems', 'Scientific research and simulation'],
    availability: 'NVIDIA announced H100 in March 2022. The Ornn series tracks the SXM model. The manufacture date of an individual rented GPU is unknown.',
    source: 'https://nvidianews.nvidia.com/news/nvidia-announces-hopper-architecture-the-next-generation-of-accelerated-computing',
  },
  H200: {
    architecture: 'Hopper', introduced: '2023-11-13', category: 'Data center GPU',
    summary: 'A Hopper GPU with 141 GB of HBM3e memory, designed to handle large amounts of data for generative AI and scientific computing.',
    uses: ['Running large language models', 'Generative AI workloads', 'Scientific computing with large datasets'],
    availability: 'Announced in November 2023, with the first systems scheduled for the second quarter of 2024. The announcement year is not the manufacture date of a rented unit.',
    source: 'https://nvidianews.nvidia.com/news/nvidia-supercharges-hopper-the-worlds-leading-ai-computing-platform',
  },
  B200: {
    architecture: 'Blackwell', introduced: '2024-03-18', category: 'Data center GPU',
    summary: 'A Blackwell accelerator used in multi-GPU systems for large AI models. Ornn reports the rental price per GPU, rather than the price of a complete system.',
    uses: ['Training large generative AI models', 'Large-scale AI inference', 'Data processing and engineering simulation'],
    availability: 'NVIDIA introduced the Blackwell platform, including B200 systems, in March 2024. This is the introduction date, not the build date of a specific rental GPU.',
    source: 'https://nvidianews.nvidia.com/news/nvidia-blackwell-platform-arrives-to-power-a-new-era-of-computing',
  },
  'RTX 5090': {
    architecture: 'Blackwell', introduced: '2025-01-06', category: 'Desktop graphics GPU',
    summary: 'A GeForce desktop GPU for gaming, creative work, and local AI applications. It serves a different mix of workloads from the data center models.',
    uses: ['Gaming and graphics rendering', 'Video and other creative work', 'Running AI tools and models locally'],
    availability: 'Announced on 6 January 2025, with retail availability from 30 January 2025. Ornn also tracks prices for rented compute on this model.',
    source: 'https://nvidianews.nvidia.com/news/nvidia-blackwell-geforce-rtx-50-series-opens-new-world-of-ai-computer-graphics',
  },
};
