
# UFM_REST_RDMA CI/CD

## Update Jenkins if proj_jjb.yaml was changed

```
  cd .ci
  make jjb
```

## Retrigger CI

Put a comment with "bot:retest"

## More details

After create Pull Request CI runs automatically.
The CI results can be found under link Details on PR page in github.

There are two main sections: Build Artifacts and Blue Ocean.

* Build Artifacts has log files with output each stage.
* On Blue Ocean page you can see a graph with CI steps. Each stage can be success(green) or fail(red).



## CI/CD 

This CD/CD  pipeline based on ci-demo. All information can be found in main ci-demo repository.

[Read more](https://github.com/Mellanox/ci-demo/blob/master/README.md)

