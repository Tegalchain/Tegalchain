# Qortal UI 

Decentralizing The World

Building and Running Qortal UI Server from source:
-----------------------------------------------------
Follow the steps below to download, install, build and run Qortal UI locally.


Installation
------------
Tools needed:
 - Node.js
 - npm
 - yarn

Clone the following repos
 - ``` git clone https://github.com/Qortal/qortal-ui.git ```
 - ``` git clone https://github.com/Qortal/qortal-ui-core.git ```
 - ``` git clone https://github.com/Qortal/qortal-ui-plugins.git ```
 - ``` git clone https://github.com/Qortal/qortal-ui-crypto.git ```

Dependency installation and linking
-----------------------------------
In `qortal-ui-core/`, `qortal-ui-plugins/`, `qortal-ui-crypto/`  directories, run: 
```
yarn install
yarn link
```

Finally, in the `qortal-ui` directory, run:
```
yarn install
yarn link qortal-ui-core
yarn link qortal-ui-plugins
yarn link qortal-ui-crypto
```



Build UI server and files
-------------------------
In `qortal-ui` directory, run:
```
yarn run build
```

Start UI Server
---------------
```
yarn run server
```


Run UI using electron
---------------------
```
yarn run start-electron
```
