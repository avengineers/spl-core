properties([
   buildDiscarder(logRotator(numToKeepStr: '20')),
   disableConcurrentBuilds()
])

node('aspl') {
    ws('aspl') {
        init()
        test()
    }
}

def init() {
    checkout scm
}

def test() {
    stage('test') {
        try {
            bat 'call build.bat --target selftests --installMandatory'
        } catch (e) {
            echo 'One or more selftests failed.'
        }
        
        junit allowEmptyResults: false, keepLongStdio: false, testResults: 'test/output/test-report.xml'
        junit allowEmptyResults: false, keepLongStdio: false, testResults: 'build/**/junit.xml'
        dir('build'){
            archiveArtifacts '**/coverage/*'
        }
    }
}
