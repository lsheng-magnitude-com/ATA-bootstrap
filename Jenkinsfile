pipeline {
  agent any
  stages {
    stage('Build') {
      parallel {
        stage('Build A') {
          steps {
            echo 'Build A'
            sleep 30
          }
        }

        stage('Build  B') {
          steps {
            echo 'Build B'
            sleep 30
          }
        }

        stage('Build C') {
          steps {
            echo 'Build C'
            sleep 30
          }
        }

      }
    }

    stage('Test') {
      parallel {
        stage('Test A') {
          steps {
            echo 'Test A'
            sleep 30
          }
        }

        stage('Test B') {
          steps {
            echo 'Test B'
            sleep 30
          }
        }

        stage('Test C') {
          steps {
            echo 'Test C'
            sleep 30
          }
        }

      }
    }

    stage('Package') {
      parallel {
        stage('Package A') {
          steps {
            echo 'Package A'
            sleep 30
          }
        }

        stage('Package B') {
          steps {
            echo 'Package B'
            sleep 30
          }
        }

        stage('Package C') {
          steps {
            echo 'Package C'
            sleep 30
          }
        }

      }
    }

  }
}