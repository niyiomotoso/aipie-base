# Episode 002 research: the graphics chips that helped change AI

**Status:** Research-backed pilot candidate. Script and final editorial choices await Niyi's approval.

## The story

In 2012, Alex Krizhevsky, working with Ilya Sutskever and Geoffrey Hinton at the University of Toronto, trained an image-classification neural network using two NVIDIA GPUs in a computer in his bedroom at his parents' home. The system, AlexNet, substantially outperformed rival entries in the ImageNet competition. This offers a human-scale opening to a wider story: how graphics processors, associated with computer games, became useful for AI research, and why NVIDIA's 2006 CUDA platform mattered.

The **protagonists** are both the researchers and NVIDIA's engineers; this is not a company advertising story. The narrative payoff is about making a technology useful beyond its original market, not a claim that NVIDIA invented AI or foresaw ChatGPT.

## Verified timeline and sources

- **1993:** NVIDIA founded, aiming to bring 3D graphics to gaming and multimedia (S1).
- **Pre-2006:** Researchers were already exploring general-purpose GPU computing; graphics chips performed large numbers of operations in parallel (S2, S3).
- **November 2006:** NVIDIA introduced CUDA, a platform and programming model to make GPUs usable for wider-purpose calculations, including research (S2, S3).
- **2011–2012:** Krizhevsky, Sutskever and Hinton worked on an ImageNet model; Krizhevsky trained it using two NVIDIA graphics cards in a bedroom computer at his parents' home (S4, S5).
- **2012:** Their ImageNet submission reached 15.3% top-five error versus 26.2% for the second-best entry (S6). This was a landmark for deep learning, not the first-ever instance of AI (S4, S5).

## Claim-to-source register

| ID | Claim | Source | Editorial note |
|---|---|---|---|
| N01 | NVIDIA started in 1993, initially focused on gaming and multimedia graphics. | S1 | Do not imply no other GPU applications existed. |
| N02 | GPUs can perform many small calculations in parallel; a simplified everyday analogy may illustrate that ability. | S2, S3 | The analogy should explain rather than claim literal mechanics. |
| N03 | CUDA, introduced in 2006, made GPUs easier to program for computing beyond graphics. | S2, S3 | CUDA was not solely designed for ChatGPT or AI. |
| N04 | AlexNet was an image **classification** system. | S4, S6 | Example: given a picture, identify the type of main subject; do not claim the 2012 model produced object bounding boxes or understood images like a human. |
| N05 | The team was Krizhevsky, Sutskever and Hinton, and the model was trained on two NVIDIA GPUs in a bedroom computer at Krizhevsky's parents' home. | S4, S5, S6 | University research, not an isolated hobby project. |
| N06 | In 2012, AlexNet performed much better than rival ImageNet entries. | S6 | The full metric is 15.3% top-five error vs 26.2%; do not conflate top-five with ordinary accuracy. |
| N07 | NVIDIA's software and GPU hardware helped enable subsequent deep-learning growth. | S2, S4, S5 | Many other researchers, algorithms and datasets mattered. |

## The plain-English test

An unfamiliar listener should be able to picture each key concept:

- **Image recognition (specifically classification):** "Imagine showing a computer a picture of a dog, and it can tell you the picture is of a dog, without you typing the answer."
- **Graphics card:** "The part of a computer that helps it draw game images quickly."
- **Parallel computing:** "Doing lots of small calculations at the same time instead of waiting for each one to finish before starting the next."
- **CUDA:** "A way for developers to use the graphics card's calculating power for jobs other than drawing game graphics."
- **AlexNet / neural network:** "The computer system the researchers trained to recognise what was in photographs." Avoid claiming a brain-like understanding.

Use at most the explanations necessary for the narrative. Plain English means easy to visualise, **not** endless definitions or slowing the story to a lecture. The phrases "that is", "in other words" and "imagine" are optional natural bridges, not compulsory filler.

## Audience involvement

An optional ending question about NVIDIA's uncertain 2006 investment offers viewers a relatable decision. Do not treat silence or lack of a question as an error; use it only if it fits Niyi's spoken flow.

## Historical and visual safeguards

- Do not imply CUDA single-handedly created modern AI or NVIDIA anticipated all later outcomes.
- Do not manufacture a photograph of the researcher's bedroom as archival evidence.
- The scene-level storyboard should come after the recorded footage has been transcribed and trimmed.
- Check rights for every historical photo, article image, logo or footage before using it.

## Sources

- **S1:** NVIDIA history, https://www.nvidia.com/en-us/about-nvidia/corporate-timeline/
- **S2:** NVIDIA CUDA technical history, https://developer.nvidia.com/blog/cuda-refresher-getting-started-with-cuda/
- **S3:** NVIDIA CUDA programming guide, https://docs.nvidia.com/cuda/archive/10.2/cuda-c-programming-guide/index.html
- **S4:** Computer History Museum, "CHM Releases AlexNet Source Code", https://computerhistory.org/blog/chm-releases-alexnet-source-code/
- **S5:** Computer History Museum, source code announcement, https://computerhistory.org/press-releases/chm-makes-alexnet-source-code-available-to-the-public/
- **S6:** Krizhevsky, Sutskever and Hinton, *ImageNet Classification with Deep Convolutional Neural Networks*, NeurIPS 2012, https://papers.nips.cc/paper/2012/file/c399862d3b9d6b76c8436e924a68c45b-Paper.pdf
