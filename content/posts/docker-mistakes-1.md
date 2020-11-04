+++
title = "Common Docker Mistakes - Episode 1"
date = 2019-04-15T10:57:55+05:30
type = "post"
description = "Sharing my Docker Learnings"
in_search_index = true
[taxonomies]
tags = ["Docker","Devops"]
+++

So, off late, I've been dabbling a lot with Docker to explore the world of containerization (too late to the party, eh?). I plan to write about some common docker gotchas. The plan is to document these learnings so they might help someone getting started with docker and also serve as a reference for myself in the future. Let me be clear, if you read the docs you will find the exact same information and there's nothing new that I have discovered. It took me some time to get around the following issues and I believe some of you might be struggling with the same. I just feel when you're starting out with completely new technology, things quickly can become overwhelming and it's A-OK to feel so. The important part is to not get intimidated by it and focus on learning the basics. Different pieces start coming together and there you have a solved puzzle :)

## The mysterious case of bind mounts and volumes

Ah! Storage. It's always not a rosy scenario whenever someone mentions storage and containers in the same sentence. Anyway, so I had this requirement where I needed 2 containers to share data. Either of the containers could modify this data, so it made for a strong use case for volumes. But for some strange reason, I decided to use bind mounts. My thought process was that I'll bind the mount path of the host to container and both of them could share the data.
Now, I know, I know all the docker veterans already facepalming so hard, but in case anyone new to docker is reading it, it works the exact way I described. The host path will be mounted ON the container, so if your host path is empty, so will your container be. It took me quite some time to figure this out because of the side effect of it. I had this line in my docker-compose:

```yaml
volumes:
  - type: bind
    source: /etc/custom/data
    target: /
```

As you can guess, I am mounting an empty folder `etc/custom/data` on the root directory of the container `/`. This was an `nginx` container and I got the weird error that `nginx` executable isn't found. It became clear that I have obviously done something wrong. After reading the documentation, it became clear that I had to use something like [Named Volumes](https://docs.docker.com/storage/volumes/) and use the same volume label for both the containers. Here's the correct docker compose example (I have removed the unnecessary fluff and only included the volumes part):

```yaml
  nginx:
    volumes:
      - type: volume
        source: assets-vol
        target: /usr/share/nginx/frontend
  frontend:
    volumes:
      - type: volume
        source: assets-vol
        target: /frontend/dist

volumes:
  assets-vol:
```

`assets-vol` is a named volume and can be managed using docker API.

## CMD vs RUN

Now, this is particularly interesting. So I have a volume mount as shown in the previous example, and quite naively I am copying some files from container 1 to container 2 at build stage. I get the error that this path doesn't exist. I am seriously reconsidering my life decisions right now.

`RUN cp /frontend/dist /usr/share/nginx/frontend`

And then it became apparent that the volume is only mounted while the container is running, not when it is building. So I had to use CMD.

`CMD cp /frontend/dist /usr/share/nginx/frontend`

Why `RUN` doesn't work and `CMD` works, you might ask? This is because that's how docker volumes are in nature. They bypass the unionFS (which is used to build docker images). UnionFS chain together a layer of images and build new images on top. Whenever you run a container from an image, a new layer is created for the container process. If you specify a path as a volume, this path doesn't get `committed` to the container data layer and is bypassed. So, TL;DR, volumes are really only accessible when the container is running and you can't access them while building.

### Epilogue

I plan to share more such silly mistakes of mine while exploring more of Docker (and hopefully running production workloads on it soon!). It really is fun though, believe me :)
