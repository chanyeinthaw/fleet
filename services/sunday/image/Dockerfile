# syntax=docker/dockerfile:1
FROM debian:bookworm-slim AS download
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates gh \
    && rm -rf /var/lib/apt/lists/*
ARG SUNDAY_VERSION=v0.0.0-nightly.5
WORKDIR /release
RUN --mount=type=secret,id=sunday-github-token,env=GH_TOKEN,required=true \
    gh release download "$SUNDAY_VERSION" --repo chanyeinthaw/sunday \
      --pattern sunday-linux-x64.tar.gz --pattern SHA256SUMS \
    && sha256sum --check SHA256SUMS \
    && tar -xzf sunday-linux-x64.tar.gz \
    && chmod 755 sunday

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=download /release/sunday /usr/local/bin/sunday
USER 1000:1000
ENTRYPOINT ["/usr/local/bin/sunday"]
CMD ["run"]
